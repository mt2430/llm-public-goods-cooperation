"""Verify file hashes and compare reproduced PDF pages with approved originals."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'reproduced')
    p.add_argument('--pdf-compare',action='store_true',help='Requires pypdfium2; compare rendered pages pixel by pixel.')
    p.add_argument('--hashes-only',action='store_true')
    args = p.parse_args()
    report={'hashes':[],'figures':[]}
    checksums = ROOT/'checksums.sha256'
    if checksums.exists():
        for line in checksums.read_text(encoding='utf8').splitlines():
            digest,rel = line.split('  ',1)
            target=ROOT/rel
            okay=target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest()==digest
            report['hashes'].append({'file':rel,'valid':okay})
        assert all(r['valid'] for r in report['hashes']), 'At least one file differs from the snapshot.'
    if args.pdf_compare and not args.hashes_only:
        import pypdfium2 as pdfium
        def raster(path):
            doc=pdfium.PdfDocument(str(path));page=doc[0]
            a=np.asarray(page.render(scale=2).to_pil().convert('RGB')).copy()
            page.close();doc.close();return a
        for original in sorted((ROOT/'figures').rglob('*.pdf')):
            rel=original.relative_to(ROOT/'figures')
            generated=args.output/'figures'/rel
            if not generated.exists():
                continue
            a,b=raster(original),raster(generated)
            same_size=a.shape==b.shape
            identical=same_size and bool(np.array_equal(a,b))
            report['figures'].append({'figure':original.stem,'same_dimensions':same_size,
                'identical_pixels':identical,'different_pixels':int(np.count_nonzero(np.any(a!=b,axis=2))) if same_size else None,
                'max_channel_difference':int(np.max(np.abs(a.astype('int16')-b.astype('int16')))) if same_size else None})
    report['all_hashes_valid']=all(r['valid'] for r in report['hashes'])
    report['all_replayed_pages_identical']=all(r['identical_pixels'] for r in report['figures']) if report['figures'] else None
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'verification_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='hashes'},indent=2))
    if report['figures'] and not report['all_replayed_pages_identical']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
