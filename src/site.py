# Wraps src/template.html into a standalone page at docs/index.html. Run from the repo root: python3 src/site.py
import re
t=open('src/template.html').read()
i=t.index('<style>');head=t[:i];body=t[i:]
head=re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>\s*','',head)
body=re.sub(r'\s*<p>Method and sources:.*?</p>','',body,flags=re.S)
body=body.replace('Prices and quarterly financials come from Yahoo Finance.','Prices and quarterly financials come from Yahoo Finance. Prices refresh about every half hour on US market days and financials once a day.')
assert 'docs.google.com' not in body and 'claude.ai/artifact' not in body.split('/*CORE*/')[0]
page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="robots" content="noindex,nofollow">'+head.strip()+'<style>:root{color-scheme:light}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style></head><body><script>window.FPW_WEB=true</script>'+body+'</body></html>'
open('docs/index.html','w').write(page);print('built docs/index.html',len(page))
