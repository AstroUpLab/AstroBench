"""Select Objaverse cabin objects by category, name and source metadata."""
import argparse
from functools import lru_cache
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]

@lru_cache(maxsize=8192)
def normalize(text):
    text = re.sub(r'([a-z]{2,})([A-Z])', r'\1 \2', str(text or ''))
    text = unicodedata.normalize('NFKC', text).casefold()
    return ' '.join(re.sub(r'[^\w]+', ' ', text, flags=re.UNICODE).replace('_', ' ').split())

@lru_cache(maxsize=1024)
def matcher(terms):
    normalized = sorted({normalize(t) for t in terms},key=len,reverse=True)
    return re.compile(r'(?<!\w)('+'|'.join(re.escape(t) for t in normalized)+r')(?:s|es)?(?!\w)')

def matched(text, terms):
    return sorted({m.group(1) for m in matcher(tuple(terms)).finditer(text)})

def contains(text, phrase):
    return bool(matcher((phrase,)).search(text))

def load_json(path):
    path = Path(path)
    with (gzip.open(path, 'rt') if path.suffix == '.gz' else path.open()) as stream:
        return json.load(stream)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def classify(uid, annotation, categories, rules):
    name = annotation.get('name') or ''
    title = normalize(name)
    cats = [normalize(c) for c in categories]
    positives = []
    for group, terms in rules['groups'].items():
        positives += [{'field':'name','term':term,'group':group} for term in matched(title,terms)]
        for cat in cats:
            for term in terms:
                if cat == normalize(term) or cat == normalize(term)+'s':
                    positives.append({'field':'lvis_category','term':term,'group':group})
    # Remove only explicit part/product phrases for negative matching. Broad tags
    # are recorded, but cannot rescue an unsuitable title or introduce a category.
    negative_title = title
    for phrase in sorted(rules['protected_phrases'], key=len, reverse=True):
        negative_title = re.sub(r'(?<!\w)'+re.escape(normalize(phrase))+r'(?!\w)', ' ', negative_title)
    negatives = [{'field':'name','term':term,'reason':reason}
                 for reason, terms in rules['exclude_names'].items()
                 for term in matched(negative_title,terms)]
    negatives += [{'field':'lvis_category','term':cat,'reason':'excluded_category'}
                  for cat in cats if cat in rules['category_exclude_exact']]
    flags = matched(title,rules['name_review_terms'])
    if any(c in rules.get('ambiguous_categories',[]) for c in cats):flags.append('ambiguous_category')
    name_groups={x['group'] for x in positives if x['field']=='name'}
    category_groups={x['group'] for x in positives if x['field']=='lvis_category'}
    if positives and not name_groups:flags.append('category_only_unrecognized_name')
    if cats and not category_groups:flags.append('unsupported_lvis_category')
    if name_groups and category_groups and not name_groups.intersection(category_groups):flags.append('category_name_group_conflict')
    for family in rules.get('tool_identity_families',[]):
        if any(c in family for c in cats) and name_groups and not any(contains(title,t) for t in family):
            flags.append('specific_tool_identity_conflict')
    if re.search(r'[&+]',name):flags.append('possible_multiple_objects')
    if annotation.get('animationCount',0): flags.append('animation_metadata')
    if len(set(cats))>1: flags.append('multiple_lvis_categories')
    if not title: flags.append('missing_name')
    ambiguous = set(rules['ambiguous_single_name_terms'])
    if positives and not any(x['field']=='lvis_category' or x['term'] not in ambiguous for x in positives):
        flags.append('ambiguous_name_only')
    # Distinguish a strongly unsuitable scene from an uncertain part or product.
    if negatives:
        if positives and all(n['reason'] in ('large_structure_or_vehicle','organic_or_deformable','excluded_category') for n in negatives):
            status,reason='review','conflicting_name_or_category'
        else: status,reason='exclude','excluded_semantics'
    elif not positives:
        coarse={x.get('name','') for x in annotation.get('categories',[]) if isinstance(x,dict)}
        if cats or coarse.intersection(rules.get('coarse_exclude_without_positive',[])):
            status,reason='exclude','category_outside_cabin_scope'
        else:status,reason='review','no_supported_name_or_category'
    elif flags:
        status,reason='review','ambiguous_or_complex_asset'
    else:
        status,reason='candidate','supported_cabin_object'
    license_value=annotation.get('license')
    slug=license_value.get('slug','') if isinstance(license_value,dict) else license_value
    pub='eligible_metadata' if slug in rules['publication_license_allowlist'] else 'hold_license'
    if annotation.get('isDownloadable') is False: pub='hold_unavailable'
    return dict(uid=uid,name=name,lvis_categories=sorted(categories),semantic_status=status,
                reason=reason,positive_matches=positives,negative_matches=negatives,review_flags=flags,
                groups=sorted({p['group'] for p in positives}),publication_status=pub,license=license_value,
                source_url=annotation.get('viewerUrl') or 'https://sketchfab.com/3d-models/'+uid,
                author={k:annotation.get('user',{}).get(k) for k in ('username','displayName','profileUrl')},
                source_categories=annotation.get('categories',[]),name_normalized=title,
                geometry_validated=False,physics_validated=False,benchmark_ready=False)

def run(metadata, lvis, rules_path, output):
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    rules=load_json(rules_path); categories=load_json(lvis); reverse=defaultdict(list)
    for cat,uids in categories.items():
        for uid in uids: reverse[uid].append(cat)
    counts=Counter(); reasons=Counter(); cat_counts=Counter(); groups=Counter(); names=Counter()
    seen=set(); candidate_uids=[]; sources=[]
    with (output/'decisions.jsonl').open('w') as all_rows, (output/'candidates.jsonl').open('w') as selected:
        for path in sorted(Path(metadata).glob('*.json.gz')):
            source=load_json(path);sources.append({'file':str(path),'sha256':sha(path),'rows':len(source)})
            for uid,a in sorted(source.items()):
                if uid in seen:raise ValueError('Duplicate source UID: '+uid)
                seen.add(uid);r=classify(uid,a,reverse.get(uid,[]),rules)
                counts[r['semantic_status']]+=1;reasons[r['reason']]+=1
                all_rows.write(json.dumps(r,ensure_ascii=False)+'\n')
                if r['semantic_status']=='candidate' and r['publication_status']=='eligible_metadata':
                    selected.write(json.dumps(r,ensure_ascii=False)+'\n');candidate_uids.append(uid)
                    groups.update(r['groups']);cat_counts.update(r['lvis_categories']);names[r['name_normalized']]+=1
                elif r['semantic_status']=='candidate':counts['candidate_license_or_availability_hold']+=1
    index_path=Path(metadata).parent/'object-paths.json.gz'
    expected=set(load_json(index_path)) if index_path.exists() else set()
    missing=sorted(expected-seen)
    (output/'missing_metadata_uids.json').write_text(json.dumps(missing))
    (output/'candidate_uids.json').write_text(json.dumps(sorted(candidate_uids),indent=2))
    report=dict(rules_version=rules['version'],rules_sha256=sha(rules_path),lvis_sha256=sha(lvis),
                metadata_sources=sources,objects_scanned=len(seen),expected_objects=len(expected) if expected else None,missing_metadata_objects=len(missing),full_index_covered=bool(expected) and seen==expected,decisions=dict(counts),reasons=dict(reasons),
                eligible_candidates=len(candidate_uids),candidate_lvis_categories=len(cat_counts),
                category_counts=dict(cat_counts.most_common()),group_counts=dict(groups),
                duplicate_candidate_names={k:v for k,v in names.items() if v>1},
                mesh_downloaded=False,benchmark_ready=False,
                qualification='Name/category screening only. Counts are object UIDs, not new semantic classes. Unknown names require review; licenses are a metadata prefilter, not a rights audit.')
    (output/'summary.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps({k:report[k] for k in ('objects_scanned','decisions','eligible_candidates','candidate_lvis_categories')}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--metadata',required=True);p.add_argument('--lvis',required=True)
    p.add_argument('--rules',default=str(ROOT/'astrobench/data/objaverse_rules.json'));p.add_argument('--output',required=True)
    a=p.parse_args();run(a.metadata,a.lvis,a.rules,a.output)
