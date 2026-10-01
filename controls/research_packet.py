"""Explicit expanded transport, separate from the frozen RQ01/QF01 files.

Rational stress-test values are stored as exact integer numerators. Invalid
reconstructions remain decodable and are adjudicated outside the decoder.
"""
from __future__ import annotations

import hashlib
import json
import lzma
import struct
import zlib

import numpy as np

HEADER = struct.Struct('<4sII5I32s')
MAX_PIXELS = 4096**2


def _zdecode(data, maximum):
    d=zlib.decompressobj(); raw=d.decompress(data,maximum+1)
    if len(raw)>maximum or not d.eof or d.unused_data or d.unconsumed_tail:
        raise ValueError('Zlib length/trailing data')
    return raw


def _pack_array(a, dtype):
    raw=np.asarray(a,dtype).tobytes()
    return lzma.compress(np.frombuffer(raw,'u1').reshape(-1,2).T.copy().tobytes(),preset=6)


def _unpack_array(data, n, dtype):
    d=lzma.LZMADecompressor(memlimit=128*(1<<20))
    raw=d.decompress(data,max_length=2*n+1)
    if len(raw)!=2*n or not d.eof or d.unused_data:
        raise ValueError('Array length/trailing data')
    return np.frombuffer(np.frombuffer(raw,'u1').reshape(2,n).T.copy().tobytes(),dtype).astype(np.int64)


def _pack_mask(mask):
    return zlib.compress(np.packbits(mask.ravel(),bitorder='little').tobytes(),9) if mask.any() else b''


def _unpack_mask(data, shape):
    n=int(np.prod(shape))
    if not data:
        return np.zeros(shape,bool)
    raw=_zdecode(data,(n+7)//8)
    if len(raw)!=(n+7)//8:
        raise ValueError('Mask size')
    bits=np.unpackbits(np.frombuffer(raw,'u1'),bitorder='little')
    if bits[n:].any():
        raise ValueError('Mask padding')
    return bits[:n].astype(bool).reshape(shape)


def _digest(y, mask, protected):
    return hashlib.sha256(np.asarray(y,'<i8').tobytes()+mask.tobytes()+protected.tobytes()).digest()


def _validate_meta(meta):
    for key in ('step','cap','denominator'):
        if type(meta.get(key)) is not int:
            raise ValueError('Integer metadata')
    if not (1<=meta['step']<=65536 and 0<=meta['cap']<=65535 and
            1<=meta['denominator']<=2**20):
        raise ValueError('Metadata range')
    if meta.get('codec') not in ('quotient-remainder-lzma6','fixed-margin-2x2'):
        raise ValueError('Transport codec')
    if meta['codec']=='fixed-margin-2x2' and (meta['cap']!=10000 or meta['denominator']!=1
        or type(meta.get('margin')) is not int or not 0<=meta['margin']<=10000):
        raise ValueError('Fixed-margin parameters')


def _assemble(y, mask, protected, meta, first, second):
    _validate_meta(meta)
    metadata=zlib.compress(json.dumps(meta,sort_keys=True,separators=(',',':'),allow_nan=False).encode(),9)
    if len(metadata)>16384:
        raise ValueError('Metadata length')
    parts=[first,second,_pack_mask(mask),_pack_mask(protected & ~mask),metadata]
    payload=HEADER.pack(b'RRF2',*y.shape,*(len(p) for p in parts),_digest(y,mask,protected))+b''.join(parts)
    packet=payload+hashlib.sha256(payload).digest()
    fees=dict(header_bytes=HEADER.size,checksum_bytes=32,quotient_or_body_bytes=len(first),
        remainder_bytes=len(second),mask_bytes=len(parts[2]),protected_bytes=len(parts[3]),
        metadata_bytes=len(metadata))
    assert sum(fees.values())==len(packet)
    return packet,fees


def encode(y, mask, step, cap, config, geo, protected=None, denominator=1):
    y=np.asarray(y); mask=np.asarray(mask,bool)
    p=mask.copy() if protected is None else np.asarray(protected,bool)|mask
    if (y.ndim!=2 or not y.size or y.size>MAX_PIXELS or min(y.shape)<1
        or y.shape!=mask.shape or p.shape!=y.shape or not np.issubdtype(y.dtype,np.integer)):
        raise ValueError('Integer numerator and masks')
    meta=dict(codec='quotient-remainder-lzma6',step=step,cap=cap,denominator=denominator,
              method=config,geo=geo,mask_semantics='excluded samples; protected union is exact')
    _validate_meta(meta)
    quotient,remainder=np.divmod(y.astype(np.int64),step)
    if quotient.min() < -32768 or quotient.max()>32767:
        raise ValueError('Signed quotient range')
    return _assemble(y,mask,p,meta,_pack_array(quotient,'<i2'),_pack_array(remainder,'<u2'))


def encode_fiber(x,mask,margin,config,geo):
    from built_area_fiber_packet import body_encode,body_decode
    x=np.asarray(x,np.int64); mask=np.asarray(mask,bool)
    if (x.ndim!=2 or not x.size or x.size>MAX_PIXELS or mask.shape!=x.shape
        or x.min()<0 or x.max()>10000 or x[mask].any() or type(margin) is not int
        or not 0<=margin<=10000):
        raise ValueError('Fixed-margin input')
    body,detail=body_encode(x,mask,margin)
    y=body_decode(body,x.shape,mask,margin).astype(np.int64)
    meta=dict(codec='fixed-margin-2x2',step=1,cap=10000,denominator=1,margin=margin,
              method=config,geo=geo,guaranteed_rectangle_bound=4*margin)
    packet,fees=_assemble(y,mask,mask,meta,body,b'')
    return packet,fees,detail


def decode(packet):
    if len(packet)<HEADER.size+32 or hashlib.sha256(packet[:-32]).digest()!=packet[-32:]:
        raise ValueError('Checksum/length')
    magic,h,w,*rest=HEADER.unpack_from(packet)
    lengths,expected=rest[:-1],rest[-1]
    if magic!=b'RRF2' or min(h,w)<1 or h*w>MAX_PIXELS or lengths[-1]>16384:
        raise ValueError('Header scope')
    if len(packet)!=HEADER.size+32+sum(lengths):
        raise ValueError('Component length')
    parts=[]; pos=HEADER.size
    for length in lengths:
        parts.append(packet[pos:pos+length]); pos+=length
    meta=json.loads(_zdecode(parts[4],65536)); _validate_meta(meta)
    mask=_unpack_mask(parts[2],(h,w)); protected=_unpack_mask(parts[3],(h,w))|mask
    if meta['codec']=='quotient-remainder-lzma6':
        q=_unpack_array(parts[0],h*w,'<i2'); r=_unpack_array(parts[1],h*w,'<u2')
        if (r>=meta['step']).any():
            raise ValueError('Remainder alphabet')
        y=(q*meta['step']+r).reshape(h,w)
    else:
        from built_area_fiber_packet import body_decode
        if parts[1] or parts[3]:
            raise ValueError('Fixed-margin components')
        y=body_decode(parts[0],(h,w),mask,meta['margin']).astype(np.int64)
    if _digest(y,mask,protected)!=expected:
        raise ValueError('Decoded digest')
    return y,mask,protected,meta
