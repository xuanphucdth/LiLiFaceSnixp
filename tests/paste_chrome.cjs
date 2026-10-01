// Real Windows clipboard paste into an isolated Chrome page; no network uploads.
const fs=require('fs');
const {chromium}=require('C:/Users/xuanp/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:false,args:['--no-first-run','--disable-sync']});
 try {
  const page=await browser.newPage();
  await page.setContent('<title>LiLiFaceSnixp clipboard test</title><h1>Local clipboard test</h1><div id="target" contenteditable="true" style="min-height:300px;border:1px solid">Paste target</div>');
  await page.evaluate(()=>{document.addEventListener('paste',async event=>{
   event.preventDefault();
   const file=[...event.clipboardData.files][0];
   if(!file){window.result={passed:false,types:[...event.clipboardData.types]};return;}
   const bitmap=await createImageBitmap(file);
   window.result={passed:bitmap.width>0&&bitmap.height>0,type:file.type,width:bitmap.width,height:bitmap.height};
  });});
  await page.locator('#target').click();
  await page.keyboard.press('Control+V');
  await page.waitForFunction(()=>window.result,{timeout:10000});
  const result=await page.evaluate(()=>window.result);
  fs.writeFileSync('test-results/chrome-paste.json',JSON.stringify(result,null,2));
  console.log(result);
  if(!result.passed)process.exitCode=1;
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1});
