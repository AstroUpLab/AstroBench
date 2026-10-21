import argparse
import json
from pathlib import Path
from .protocol import make_plan, validate_plan, score_trace
from .metrics import aggregate_results, IDENTITY_FIELDS
from .inventory import object_inventory, scene_catalog, select_catalog
from .workcells import (workcell_catalog, make_workcell_plan, validate_workcell_plan,
                        score_workcell_trace, aggregate_workcell_results)
from .workcell_assets import check_workcell_assets


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
    parser = argparse.ArgumentParser(description='AstroBench object catalogs, episode plans and scoring')
    sub = parser.add_subparsers(dest='command', required=True)
    plan = sub.add_parser('plan'); plan.add_argument('catalog'); plan.add_argument('--seed',type=int,default=0)
    plan.add_argument('--object-set', choices=('core20','objaverse8414','custom'), default='core20')
    objects = sub.add_parser('objects', help='Export an object inventory')
    objects.add_argument('--object-set', choices=('core20','objaverse8414'), default='core20')
    scenes = sub.add_parser('scenes', help='Export cabin scene configuration')
    score = sub.add_parser('score'); score.add_argument('plan'); score.add_argument('episode_id'); score.add_argument('trace')
    report = sub.add_parser('report'); report.add_argument('plan'); report.add_argument('results')
    workcells = sub.add_parser('workcells', help='Export MELFI and RRM workcell tasks')
    workcells.add_argument('--asset-root', help='Verify manifests in a local assets/workcells directory')
    workcell_plan = sub.add_parser('workcell-plan', help='Plan selected workcell tasks and targets')
    workcell_plan.add_argument('--workcell', choices=('all', 'melfi_v6', 'rrm_tb1'), default='all')
    workcell_plan.add_argument('--task', action='append', help='Task ID; repeat to select several')
    workcell_plan.add_argument('--target', action='append', help='Target ID; requires exactly one --task')
    workcell_plan.add_argument('--repeats', type=int, default=1)
    workcell_plan.add_argument('--seed', type=int, default=0)
    workcell_plan.add_argument('--asset-root', help='Verify local asset manifests')
    workcell_score = sub.add_parser('workcell-score', help='Score a synchronized workcell observation trace')
    workcell_score.add_argument('plan'); workcell_score.add_argument('episode_id'); workcell_score.add_argument('trace')
    workcell_score.add_argument('--asset-root', help='Verify the active target in canonical or same-source variant assets')
    workcell_report = sub.add_parser('workcell-report', help='Aggregate all planned workcell episodes')
    workcell_report.add_argument('plan'); workcell_report.add_argument('results')
    workcell_assets = sub.add_parser('workcell-check-assets', help='Verify workcell files and asset identities')
    workcell_assets.add_argument('asset_root')
    for command in (plan,score,report,objects,scenes,workcells,workcell_plan,workcell_score,workcell_report,workcell_assets):
        command.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'workcells': result = workcell_catalog(asset_root=args.asset_root)
    elif args.command == 'workcell-check-assets':
        workcell_catalog(asset_root=args.asset_root)
        result = check_workcell_assets(args.asset_root)
    elif args.command == 'workcell-plan':
        if args.target and (not args.task or len(args.task) != 1):
            raise ValueError('--target requires exactly one --task')
        targets = {args.task[0]: args.target} if args.target else None
        result = make_workcell_plan(args.task, repeats=args.repeats, seed=args.seed, targets=targets,
                                   workcell=None if args.workcell == 'all' else args.workcell,
                                   asset_root=args.asset_root)
    elif args.command in ('workcell-score', 'workcell-report'):
        frozen = validate_workcell_plan(read(args.plan))
        if args.command == 'workcell-report': result = aggregate_workcell_results(frozen, read(args.results))
        else:
            ep = next((e for e in frozen['episodes'] if e['episode_id'] == args.episode_id), None)
            if ep is None: raise ValueError('unknown workcell episode_id')
            trace = read(args.trace)
            if trace.get('episode_id') != ep['episode_id'] or trace.get('spec_hash') != ep['spec_hash']:
                raise ValueError('trace identity mismatch')
            result = score_workcell_trace(ep, trace['samples'], asset_root=args.asset_root)
    elif args.command == 'objects': result = object_inventory(args.object_set)
    elif args.command == 'scenes': result = scene_catalog()
    elif args.command == 'plan': result = make_plan(select_catalog(read(args.catalog), args.object_set), args.seed)
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
