"""Source-free RQ01 full decode and common SUM/count endpoint."""
import argparse
import json
from pathlib import Path
import resource
import time

import numpy as np
from range_rect_quant.packet import decode
from built_area_metrics import cache, query


def main():
    p = argparse.ArgumentParser()
    p.add_argument('packet', type=Path); p.add_argument('output', type=Path)
    p.add_argument('report', type=Path); p.add_argument('--queries', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or args.report.exists():
        raise SystemExit('Refusing to overwrite output')
    start = time.perf_counter()
    y, mask, meta, zero_protect = decode(args.packet.read_bytes())
    decoded = time.perf_counter()
    cached = cache(y, mask)
    q = np.load(args.queries, allow_pickle=False)
    first = list(query(cached, q[0])); first_done = time.perf_counter()
    warm = time.perf_counter()
    answers = [dict(zip(('sum', 'count'), query(cached, r))) for r in q]
    warm_seconds = time.perf_counter() - warm
    np.savez_compressed(args.output, y=y, mask=mask, zero_protect=zero_protect)
    args.report.write_text(json.dumps(dict(status='DECODED', source_provided=False,
        prefix_state_provided=False, meta=meta, decode_seconds=decoded-start,
        first_query=first, first_query_completed_perf_counter=first_done,
        warm_1024_query_seconds=warm_seconds, answers=answers,
        cache_bytes=cached[0].nbytes+cached[1].nbytes,
        process_peak_rss_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        rss_scope='macOS self peak bytes; single instrumented run'),indent=2)+'\n')


if __name__ == '__main__':
    main()
