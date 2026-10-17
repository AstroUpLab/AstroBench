"""Fetch pinned official metadata only, resumably with bounded attempts/workers."""
import argparse,concurrent.futures,gzip,hashlib,json,re,urllib.request
from pathlib import Path

def main(cache,workers,revision):
 p=Path(cache);p.mkdir(parents=True,exist_ok=True);(p/'metadata').mkdir(exist_ok=True)
 if not re.fullmatch('[0-9a-f]{40}',revision):raise ValueError('Expected pinned revision')
 source_path=p/'source.json'
 if not source_path.exists():source_path.write_text(json.dumps({'repo':'allenai/objaverse','revision':revision},indent=2))
 source=json.loads(source_path.read_text());rev=source['revision']
 if rev!=revision:raise ValueError('Cache revision mismatch')
 for name in ('object-paths.json.gz','lvis-annotations.json.gz'):
  dst=p/name
  if not dst.exists():
   with urllib.request.urlopen(f'https://huggingface.co/datasets/allenai/objaverse/resolve/{rev}/{name}',timeout=120) as response:data=response.read()
   json.loads(gzip.decompress(data));tmp=dst.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(dst)
 if not re.fullmatch('[0-9a-f]{40}',rev):raise ValueError('Expected pinned revision')
 with gzip.open(p/'object-paths.json.gz','rt') as f:paths=json.load(f)
 shards=sorted({v.split('/')[1] for v in paths.values()})
 if any(not re.fullmatch(r'\d{3}-\d{3}',s) for s in shards):raise ValueError('Invalid shard')
 def fetch(shard):
  dst=p/'metadata'/(shard+'.json.gz');url=f'https://huggingface.co/datasets/allenai/objaverse/resolve/{rev}/metadata/{shard}.json.gz'
  if dst.exists():
   try:
    with gzip.open(dst,'rt') as f: rows=json.load(f)
    return dict(shard=shard,status='cached',rows=len(rows),sha256=hashlib.sha256(dst.read_bytes()).hexdigest())
   except (OSError,ValueError):raise ValueError('Corrupt cached metadata: '+str(dst))
  for attempt in range(2):
   try:
    with urllib.request.urlopen(url,timeout=120) as response:data=response.read()
    obj=json.loads(gzip.decompress(data));tmp=dst.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(dst)
    return dict(shard=shard,status='downloaded',rows=len(obj),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
   except Exception as e: error=repr(e)
  return dict(shard=shard,status='failed',error=error)
 receipts=[]
 prior=p/'download_receipt.json'
 if prior.exists():
  import time
  prior.rename(p/('download_receipt_'+str(time.time_ns())+'.json'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
  for r in pool.map(fetch,shards):
   receipts.append(r)
   (p/'download_receipt.json').write_text(json.dumps(dict(revision=rev,expected_shards=len(shards),completed=len(receipts),shards=receipts),indent=2))
   if len(receipts)%20==0 or r['status']=='failed':print(len(receipts),'/',len(shards),r['status'],flush=True)
 print('finished',len(receipts),'failed',sum(r['status']=='failed' for r in receipts),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--cache',required=True);a.add_argument('--workers',type=int,default=6);a.add_argument('--revision',default='556637099bf4fa79ea7b239d0d9c328b8a2e9ac8');v=a.parse_args()
 if not 1<=v.workers<=8:raise ValueError('workers must be 1..8')
 main(v.cache,v.workers,v.revision)
