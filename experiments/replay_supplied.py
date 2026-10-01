"""Re-encode supplied saved synthetic arrays without overwriting the archive."""
import json
from pathlib import Path
import numpy as np
from range_rect_quant.packet import pack_u16
from verify_saved import independent_rectangle_max
from run_pilot import ROOT,write_json,verify_preserved


def main():
    output=ROOT/'integration/checks/supplied_replay_20261001.json'
    if output.exists():raise SystemExit('Refusing to overwrite local replay')
    folder=ROOT/'supplied/LinewiseROI_plan_20261001/results';checks=[]
    for filename,prefix in (('synthetic_screen.json',''),('scale_screen.json','scale_')):
        for row in json.loads((folder/filename).read_text())['rows']:
            path=folder/(prefix+row['synthetic_source']+'_'+str(row['epsilon'])+'.npz')
            with np.load(path,allow_pickle=False) as z:x,y=z['x'],z['y']
            error=int(independent_rectangle_max(y-x));step=row['step']
            if error!=row['exact_max_rectangle'] or int(np.count_nonzero(y%step))!=row['off_lattice'] or np.any((y<0)|(y>10000)):raise ValueError('Supplied saved field')
            for key,a in (('raw_lossless_payload_bytes',x),('coarse_payload_bytes',y//step),('fine_payload_bytes',y%step)):
                if len(pack_u16(a))!=row[key]:raise ValueError('Supplied payload length mismatch: '+key)
            checks.append(dict(file=str(path.relative_to(ROOT)),independent_rectangle_error=error,actual_payload_lengths_match=True,
                changed=int(np.count_nonzero(y!=x)),checkerboard_representation_only=bool(row['synthetic_source']=='checkerboard_extremes')))
    write_json(output,dict(status='PASS_SAVED_SYNTHETIC_PAYLOAD_REPLAY',cases=len(checks),checks=checks,preserved=verify_preserved(),
        not_fresh_optimizer_execution=True,not_cold_scientific_stream=True,source_environment_python='3.13.5/Linux',local_environment_python='3.12.14/macOS'))
    print('PASS',len(checks),'supplied saved synthetic arrays; payload replay only',flush=True)


if __name__=='__main__':main()
