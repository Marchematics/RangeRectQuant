"""Paid native baseline files for percentage fields (RWS1, not BA02)."""
import hashlib
from io import BytesIO
import json
import lzma
import struct
import zlib

import numpy as np
from PIL import Image
from controls.research_packet import _pack_mask,_unpack_mask,_zdecode
from built_area_discrete_packet import grid,body_codec

HEADER=struct.Struct('<4sIIIII32s')


def water_grid():
    rows=grid()
    for cfg in rows:
        if cfg['backend']=='qpet': cfg['base_bound']=100.
    rows += [dict(backend='u8-lzma',predictor=p,preset=6) for p in ('raw','row')]
    rows += [dict(backend='u8-png')]
    return rows


def digest(y,mask):
    return hashlib.sha256(np.asarray(y,'<i8').tobytes()+mask.tobytes()).digest()


def codec(cfg,operation,data,shape,commands):
    if cfg['backend']=='u8-lzma':
        if operation=='encode':
            a=np.asarray(data,np.int64)
            if cfg['predictor']=='row':
                d=a.copy(); d[:,1:]-=a[:,:-1]; a=np.where(d>=0,2*d,-2*d-1)
            if a.min()<0 or a.max()>255: raise ValueError('Byte predictor range')
            return lzma.compress(a.astype('u1').tobytes(),preset=6)
        n=int(np.prod(shape)); decoder=lzma.LZMADecompressor(memlimit=128*(1<<20))
        raw=decoder.decompress(data,max_length=n+1)
        if len(raw)!=n or not decoder.eof or decoder.unused_data: raise ValueError('Byte body length')
        a=np.frombuffer(raw,'u1').astype(np.int64).reshape(shape)
        if cfg['predictor']=='row': a=np.where(a%2,-(a//2)-1,a//2).cumsum(1)
        return a
    if cfg['backend']=='u8-png':
        if operation=='encode':
            b=BytesIO(); Image.fromarray(np.asarray(data,'u1')).save(b,format='PNG',compress_level=9)
            return b.getvalue()
        with Image.open(BytesIO(data)) as image: a=np.asarray(image).astype(np.int64)
        if a.shape!=shape: raise ValueError('PNG shape')
        return a
    return body_codec(cfg,operation,data,shape,commands)


def roundback(a,mask):
    if a.shape!=mask.shape or not np.isfinite(a).all(): raise ValueError('Finite decoded native shape')
    y=np.clip(np.rint(a),0,100).astype(np.int64); y[mask]=0
    return y


def encode(x,mask,cfg,geo,commands):
    x=np.asarray(x,np.int64); mask=np.asarray(mask,bool)
    if (cfg not in water_grid() or x.ndim!=2 or not x.size or x.size>1024**2
        or mask.shape!=x.shape or x.min()<0 or x.max()>100 or x[mask].any()):
        raise ValueError('Percentage source and frozen native config')
    body=codec(cfg,'encode',x,x.shape,commands)
    y=roundback(codec(cfg,'decode',body,x.shape,commands),mask)
    metadata=dict(codec=cfg,geo=geo,cap=100,units='percentage-point sums',
                  postprocess='nearest-even integer;clip [0,100];missing zero')
    config=zlib.compress(json.dumps(metadata,sort_keys=True,separators=(',',':')).encode(),9)
    mb=_pack_mask(mask)
    payload=HEADER.pack(b'RWS1',*x.shape,len(mb),len(config),len(body),digest(y,mask))+mb+config+body
    blob=payload+hashlib.sha256(payload).digest()
    return blob,dict(header_bytes=HEADER.size,checksum_bytes=32,mask_bytes=len(mb),
                     metadata_bytes=len(config),body_bytes=len(body))


def decode(blob,commands):
    if len(blob)<HEADER.size+32 or hashlib.sha256(blob[:-32]).digest()!=blob[-32:]: raise ValueError('RWS1 checksum')
    magic,h,w,ml,cl,bl,expected=HEADER.unpack_from(blob)
    if magic!=b'RWS1' or min(h,w)<1 or h*w>1024**2 or cl>16384 or len(blob)!=HEADER.size+32+ml+cl+bl:
        raise ValueError('RWS1 dimensions/length')
    pos=HEADER.size; mask=_unpack_mask(blob[pos:pos+ml],(h,w)); pos+=ml
    meta=json.loads(_zdecode(blob[pos:pos+cl],65536)); pos+=cl
    if meta['codec'] not in water_grid() or meta['cap']!=100 or meta['units']!='percentage-point sums':
        raise ValueError('Native percentage configuration')
    if meta['postprocess']!='nearest-even integer;clip [0,100];missing zero': raise ValueError('Postprocess')
    y=roundback(codec(meta['codec'],'decode',blob[pos:pos+bl],(h,w),commands),mask)
    if digest(y,mask)!=expected: raise ValueError('Decoded percentage digest')
    return y,mask,mask.copy(),meta
