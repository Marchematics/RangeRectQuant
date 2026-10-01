"""Source-free QF01 decoder and the same fixed SUM/count endpoint."""
import argparse
import json
from pathlib import Path
import time

import numpy as np
from controls.field_packet import decode
from built_area_metrics import cache, query


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('packet', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('--queries', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.report.exists():
        raise SystemExit('Refusing to overwrite output')
    started = time.perf_counter()
    y, mask, meta, zero = decode(args.packet.read_bytes())
    cached = cache(y, mask)
    q = np.load(args.queries, allow_pickle=False)
    first = query(cached, q[0])
    cold = time.perf_counter()-started
    answers = [dict(zip(('sum', 'count'), query(cached, r))) for r in q]
    np.savez_compressed(args.output, y=y, mask=mask, zero_protect=zero)
    args.report.write_text(json.dumps(dict(
        status='DECODED', source_provided=False, prefix_state_provided=False,
        meta=meta, first_query=first, answers=answers, cold_decode_cache_first_query_seconds=cold),
        indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
