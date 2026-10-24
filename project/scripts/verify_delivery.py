"""Recheck exported numbers, source hashes and deliverable containers."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone

import fitz
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    checks = []

    def check(name, ok):
        if not bool(ok):
            raise AssertionError(name)
        checks.append({"name": name, "passed": True})

    summary = json.loads((ROOT / 'results/summary.json').read_text())
    pred = pd.read_csv(ROOT / 'results/predictions.csv')
    check('test_rows', len(pred) == summary['splits']['test'] == 2193)
    for key, expected in summary['metrics'].items():
        residual = pred.et0 - pred[key]
        values = dict(mae=abs(residual).mean(), rmse=np.sqrt((residual**2).mean()),
                      r2=1-(residual**2).sum()/((pred.et0-pred.et0.mean())**2).sum())
        for metric, value in values.items():
            check(f'{key}_{metric}', abs(value-expected[metric]) < 1e-7)
    coverage = ((pred.et0 >= pred.lower) & (pred.et0 <= pred.upper)).mean()
    check('coverage', abs(coverage-summary['interval']['all']['coverage']) < 1e-10)
    check('input_dates_before_target', (pd.to_datetime(pred.latest_input_date) < pd.to_datetime(pred.date)).all())

    scenarios = pd.read_csv(ROOT / 'results/simulation_scenarios.csv')
    daily = pd.read_csv(ROOT / 'results/simulation_daily.csv')
    keys = ['site', 'year', 'taw', 'eta', 'policy']
    totals = daily.groupby(keys).agg(irrigation_mm=('gross_mm','sum'), stress_days=('stress','sum'),
                                    drainage_mm=('drainage','sum'), unmet_mm=('unmet','sum'))
    check('180_unique_scenarios', len(scenarios) == len(totals) == 180 and not scenarios.duplicated(keys).any())
    merged = scenarios.set_index(keys).join(totals, rsuffix='_recomputed')
    for metric in ['irrigation_mm','stress_days','drainage_mm','unmet_mm']:
        check('daily_to_scenario_'+metric, np.allclose(merged[metric],merged[metric+'_recomputed'],atol=1e-4,rtol=0))
    central = scenarios[(scenarios.taw == 120) & (scenarios.eta == .85)].groupby('policy').mean(numeric_only=True)
    for policy, expected in summary['simulation']['central'].items():
        for metric, value in expected.items():
            check(f'central_{policy}_{metric}', abs(central.loc[policy,metric]-value) < 5.01e-5)

    sources = json.loads((ROOT / 'inputs/provenance.json').read_text())
    for source in sources:
        check('sha256_'+source['file'], hashlib.sha256((ROOT/source['file']).read_bytes()).hexdigest() == source['sha256'])
    pdfs = {}
    for name, pages in [('墒策_技术方案',33),('墒策_佐证材料',4),('墒策_答辩演示',15)]:
        file = ROOT / f'materials/{name}.pdf'
        doc = fitz.open(file)
        check(name+'_pages', len(doc) == pages)
        check(name+'_text', all(len(p.get_text().strip()) > 20 for p in doc))
        pdfs[name] = {'pages':len(doc),'bytes':file.stat().st_size}
    check('technical_pdf_under_10MB', pdfs['墒策_技术方案']['bytes'] < 10_000_000)
    with zipfile.ZipFile(ROOT/'materials/墒策_答辩演示.pptx') as z:
        check('pptx_crc', z.testzip() is None)
        check('pptx_15_slides', sum(n.startswith('ppt/slides/slide') and n.endswith('.xml') for n in z.namelist()) == 15)
        check('pptx_image_present', any(n.startswith('ppt/media/') for n in z.namelist()))

    ffprobe = shutil.which('ffprobe')
    ffmpeg = shutil.which('ffmpeg')
    if not ffprobe or not ffmpeg:
        raise RuntimeError('Video verification requires ffprobe and ffmpeg')
    video = ROOT/'materials/墒策_演示视频.mp4'
    info = json.loads(subprocess.check_output([ffprobe,'-v','error','-show_entries','format=duration,size:stream=codec_type,codec_name,width,height','-of','json',str(video)]))
    check('video_3_to_5_minutes', 180 <= float(info['format']['duration']) <= 300)
    check('video_under_300MB', video.stat().st_size < 300_000_000)
    check('video_and_audio_streams', {s['codec_type'] for s in info['streams']} == {'audio','video'})
    decode = subprocess.run([ffmpeg,'-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True)
    check('video_full_decode', decode.returncode == 0 and not decode.stderr.strip())
    browser = json.loads((ROOT/'results/browser_checks.json').read_text())
    check('browser_checks', len(browser['checks']) == 9 and all(c['passed'] for c in browser['checks']) and not browser['errors'])
    result = {'checked_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'pdfs':pdfs,'video':info,
              'scope':'本地文件核验：指标重算、仿真汇总一致性、原始数据哈希、文档与视频完整性。'}
    (ROOT/'results/delivery_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(f'{len(checks)} delivery checks passed')


if __name__ == '__main__':
    main()
