const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),app=path.join(root,'app');
const page=fs.readFileSync(path.join(app,'prestamodesk-workspace.html'),'utf8');
assert(!/<iframe|<style|style=|onclick=/.test(page));
for(const match of page.matchAll(/(?:src|href)="(\/assets\/[^" ]+)"/g))assert(fs.existsSync(path.join(app,match[1])));
const sources=[...page.matchAll(/<script src="([^"]+)"/g)].map(x=>fs.readFileSync(path.join(app,x[1]),'utf8'));
for(const code of sources)new vm.Script(code);
assert(!/\beval\s*\(|new Function\s*\(/.test(sources.join('\n')));
assert(!/portfolioImport|administration\/imports|c2e4f6a8b0d3/.test(sources.join('\n')),'cancelled import found');
const context={window:{}};vm.createContext(context);vm.runInContext(sources[0],context);
for(const [key,screen] of Object.entries(context.window.PrestamoDeskScreens)){
 assert.equal(typeof screen.start,'function');assert(!/<script/.test(screen.html));
 const ids=[...screen.html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);assert.equal(ids.length,new Set(ids).size,key+' duplicate IDs');
}
const nginx=fs.readFileSync(path.join(root,'nginx/default.conf'),'utf8'),staging=fs.readFileSync(path.join(root,'staging/nginx.conf'),'utf8');
for(const config of [nginx,staging]){assert.match(config,/location = \/prestamodesk\/workspace/);assert.match(config,/try_files \/prestamodesk-workspace.html =404/);assert.match(config,/frame-src 'none'/);assert.match(config,/frame-ancestors 'none'/);}
assert.match(nginx,/app\|workspace\|caja/);assert.match(staging,/\/prestamodesk-workspace.html "default-src/);
console.log('Workspace structural checks passed: compiled sections, assets, scoped IDs, routes, strict frame policy, no cancelled import.');
