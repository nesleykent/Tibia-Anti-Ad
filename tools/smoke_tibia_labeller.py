"""Exercise real local inference on public acceptance metadata, without publishing."""
import json
from tibia_learning import ROOT, verify_labeller, label_batch, StageError


def smoke():
    verify_labeller()
    cases = json.loads((ROOT / 'tests/data/tibia-span-heldout-acceptance.json').read_text())['cases']
    cases = [dict(title=r['title'], tags=r['tags'], private=True) for r in cases]
    cases.extend([
        dict(title='Padventures - Event Halloween', tags=['PAD', 'PadventuresDiamond', 'Español'], private=True),
        dict(title='hunt bosses', tags=['English'], private=False),
    ])
    for start in range(0, len(cases), 4):
        batch = cases[start:start + 4]
        results = label_batch(batch)
        if any(r['private'] != c['private'] for r, c in zip(results, batch)):
            raise StageError('Local labeller semantic smoke check failed')
    print('Local inference passed 8 public semantic controls without API credentials')


if __name__ == '__main__':
    try:
        smoke()
    except StageError as error:
        raise SystemExit(str(error)) from None
