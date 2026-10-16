import argparse
import json
from pathlib import Path
from .protocol import make_plan, validate_plan, score_trace
from .metrics import aggregate_results, IDENTITY_FIELDS


def read(path):
    def unique(pairs):
        out = {}
        for k,v in pairs:
            if k in out: raise ValueError('duplicate JSON key: '+k)
            out[k] = v
        return out
    def reject(v): raise ValueError('nonfinite JSON: '+v)
    return json.loads(Path(path).read_text(), object_pairs_hook=unique, parse_constant=reject)


def main():
    parser = argparse.ArgumentParser(description='AstroBench CPU protocol tools; no simulator')
    sub = parser.add_subparsers(dest='command', required=True)
    plan = sub.add_parser('plan'); plan.add_argument('catalog'); plan.add_argument('--seed',type=int,default=0)
    score = sub.add_parser('score'); score.add_argument('plan'); score.add_argument('episode_id'); score.add_argument('trace')
    report = sub.add_parser('report'); report.add_argument('plan'); report.add_argument('results')
    for command in (plan,score,report): command.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'plan': result = make_plan(read(args.catalog), args.seed)
    else:
        frozen = validate_plan(read(args.plan))
        if args.command == 'report': result = aggregate_results(frozen, read(args.results))
        else:
            ep = next((e for e in frozen['episodes'] if e['episode_id']==args.episode_id), None)
            if ep is None: raise ValueError('unknown episode_id')
            trace = read(args.trace)
            if trace['episode_id'] != ep['episode_id'] or trace['spec_hash'] != ep['spec_hash']:
                raise ValueError('trace identity mismatch')
            result = {**{k:ep[k] for k in IDENTITY_FIELDS}, 'status':'completed',
                      **score_trace(trace['samples'], ep['protocol'])}
    with Path(args.output).open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')


if __name__ == '__main__': main()
