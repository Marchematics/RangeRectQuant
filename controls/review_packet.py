"""Uniform paid transport for representation and hierarchy comparisons."""
import hashlib
import json
import lzma
import zlib
import numpy as np
from controls.research_packet import HEADER,MAX_PIXELS,_pack_mask,_unpack_mask,_digest,_zdecode
from controls.hierarchical_sum import transform,inverse

LAYOUTS=('direct','shuffled','split','quotient-only','hierarchical')


def _encode_array(a,dtype,shuffle):
    raw=np.asarray(a,dtype).tobytes();width=np.dtype(dtype).itemsize
    if shuffle:raw=np.frombuffer(raw,'u1').reshape(-1,width).T.copy().tobytes()
    return lzma.compress(raw,preset=6)


def _decode_array(data,n,dtype,shuffle):
    width=np.dtype(dtype).itemsize;decoder=lzma.LZMADecompressor(memlimit=128*(1<<20))
    raw=decoder.decompress(data,max_length=n*width+1)
    if len(raw)!=n*width or not decoder.eof or decoder.unused_data:raise ValueError('Array length/trailing data')
    if shuffle:raw=np.frombuffer(raw,'u1').reshape(width,n).T.copy().tobytes()
    return np.frombuffer(raw,dtype).astype(np.int64)


def encode(y,mask,step,layout,method,geo,protected=None,cap=10000):
    y=np.asarray(y,np.int64);mask=np.asarray(mask,bool)
    p=mask.copy() if protected is None else np.asarray(protected,bool)|mask
    if (y.ndim!=2 or not y.size or y.size>MAX_PIXELS or mask.shape!=y.shape or p.shape!=y.shape
            or type(step) is not int or not 1<=step<=65535 or not 0<=cap<=65535
            or y.min()<0 or y.max()>cap or y[mask].any() or layout not in LAYOUTS):
        raise ValueError('Representation input')
    second=b'';actual=y
    if layout in ('split','quotient-only'):
        q,r=np.divmod(y,step);first=_encode_array(q,'<u2',True)
        if layout=='split':second=_encode_array(r,'<u2',True)
        else:actual=q*step
    elif layout=='hierarchical':first=_encode_array(transform(y,mask),'<i8',True)
    else:first=_encode_array(y,'<u2',layout=='shuffled')
    meta=dict(layout=LAYOUTS.index(layout),step=step,cap=cap,method=method,geo=geo,denominator=1)
    metadata=zlib.compress(json.dumps(meta,sort_keys=True,separators=(',',':'),allow_nan=False).encode(),9)
    parts=[first,second,_pack_mask(mask),_pack_mask(p&~mask),metadata]
    payload=HEADER.pack(b'RRA3',*y.shape,*(len(b) for b in parts),_digest(actual,mask,p))+b''.join(parts)
    blob=payload+hashlib.sha256(payload).digest()
    fees=dict(header_bytes=HEADER.size,checksum_bytes=32,quotient_or_body_bytes=len(first),
              remainder_bytes=len(second),mask_bytes=len(parts[2]),protected_bytes=len(parts[3]),metadata_bytes=len(metadata))
    assert sum(fees.values())==len(blob)
    return blob,fees


def decode(blob):
    if len(blob)<HEADER.size+32 or hashlib.sha256(blob[:-32]).digest()!=blob[-32:]:raise ValueError('Checksum')
    magic,h,w,*tail=HEADER.unpack_from(blob);lengths,digest=tail[:-1],tail[-1]
    if magic!=b'RRA3' or min(h,w)<1 or h*w>MAX_PIXELS or len(blob)!=HEADER.size+32+sum(lengths) or lengths[-1]>16384:
        raise ValueError('Header')
    parts=[];position=HEADER.size
    for n in lengths:parts.append(blob[position:position+n]);position+=n
    meta=json.loads(_zdecode(parts[-1],65536));layout=meta.get('layout');step=meta.get('step');cap=meta.get('cap')
    if type(layout) is not int or not 0<=layout<len(LAYOUTS) or type(step) is not int or not 1<=step<=65535 or type(cap) is not int or not 0<=cap<=65535:
        raise ValueError('Metadata')
    mask=_unpack_mask(parts[2],(h,w));p=_unpack_mask(parts[3],(h,w))|mask
    if layout==4:y=inverse(_decode_array(parts[0],h*w,'<i8',True),mask)
    else:
        y=_decode_array(parts[0],h*w,'<u2',layout!=0).reshape(h,w)
        if layout==2:
            remainder=_decode_array(parts[1],h*w,'<u2',True).reshape(h,w)
            if (remainder>=step).any():raise ValueError('Remainder alphabet')
            y=y*step+remainder
        elif layout==3:y=y*step
    if layout!=2 and parts[1]:raise ValueError('Unexpected remainder stream')
    if y.min()<0 or y.max()>cap or y[mask].any() or _digest(y,mask,p)!=digest:raise ValueError('Decoded field/digest')
    return y,mask,p,meta
