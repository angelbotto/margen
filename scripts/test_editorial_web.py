#!/usr/bin/env python3
"""Offline browser checks for the opt-in website shell and embedded recipe."""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

class EditorialWeb(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch()
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.pw.stop()
 def page(self,width=1440,motion='no-preference',js=True,embedded=False):
  context=self.browser.new_context(viewport={'width':width,'height':1000},reduced_motion=motion,java_script_enabled=js);self.addCleanup(context.close)
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));requests=[];page.on('request',lambda r:requests.append(r.url))
  if embedded:
   html='<style>'+(ROOT/'packages/core/styles/artifact.css').read_text()+'</style>'+(ROOT/'packages/core/recipes/web-shell/example.html').read_text()+'<script>'+(ROOT/'packages/core/components/editorial-pieces.js').read_text()+'</script>'
  else:html=(ROOT/'examples/generated/editorial-web.html').read_text()
  page.set_content(html);page.evaluate('document.fonts.ready') if js else None
  return page,errors,requests
 def test_desktop_and_mobile_geometry(self):
  for width in (300,320,390,640,768,1024,1440):
   with self.subTest(width=width):
    page,errors,requests=self.page(width)
    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
    box=page.locator('.web-navegacion').bounding_box()
    if width<640:self.assertEqual(box['y']+box['height'],984)
    else:self.assertEqual(box['y'],0)
    title=page.locator('h1');self.assertEqual(title.count(),1);self.assertEqual(title.bounding_box()['y'],96)
    self.assertEqual(title.evaluate('e=>getComputedStyle(e).fontSize'),'36.4px' if width<640 else '44.5px')
    self.assertEqual(title.evaluate('e=>getComputedStyle(e).lineHeight'),'43.68px' if width<640 else '49.4444px')
    nav=page.locator('.web-navegacion nav').bounding_box()
    self.assertEqual(nav['width'],min(1024,width-48))
    if width<640:self.assertEqual(nav['y']+nav['height'],984)
    else:self.assertEqual(nav['y'],16)
    self.assertEqual(page.locator('.web-prosa').first.bounding_box()['width'],min(528,width-48))
    self.assertEqual(page.locator('.web-pie').evaluate('e=>getComputedStyle(e).position'),'sticky')
    self.assertEqual(errors,[]);self.assertEqual(requests,[])
    if width in (390,1440):page.screenshot(path=f'/tmp/margen-web-{width}.png')
    page.close()
 def test_scroll_focus_and_footer(self):
  page,errors,_=self.page(390)
  page.evaluate('scrollTo({top:250,behavior:"instant"})');page.wait_for_timeout(100)
  self.assertTrue(page.locator('body').evaluate('e=>e.classList.contains("web-nav-oculta")'))
  link=page.locator('.web-navegacion a').first;link.focus()
  self.assertEqual(page.locator('.web-navegacion').evaluate('e=>getComputedStyle(e).opacity'),'1')
  self.assertEqual(page.locator('.web-navegacion').evaluate('e=>getComputedStyle(e).filter'),'none')
  link.blur();page.evaluate('scrollTo({top:100,behavior:"instant"})');page.wait_for_timeout(100)
  self.assertFalse(page.locator('body').evaluate('e=>e.classList.contains("web-nav-oculta")'))
  footerLink=page.locator('.web-pie nav a').first;footerLink.focus()
  self.assertTrue(footerLink.is_visible());self.assertEqual(page.locator('.web-pie').evaluate('e=>getComputedStyle(e).zIndex'),'4')
  footerLink.click();self.assertEqual(page.evaluate('document.activeElement.id'),'web-lecturas')
  self.assertEqual(errors,[])
 def test_footer_reveals_beneath_main(self):
  page,_,_=self.page();main=page.locator('.web-contenido');footer=page.locator('.web-pie')
  initialMain=main.bounding_box();initialFooter=footer.bounding_box()
  self.assertLess(initialFooter['y'],initialMain['y']+initialMain['height'])
  page.evaluate('scrollTo({top:document.documentElement.scrollHeight,behavior:"instant"})');page.wait_for_timeout(80)
  finalMain=main.bounding_box();finalFooter=footer.bounding_box()
  self.assertAlmostEqual(finalMain['y']+finalMain['height'],finalFooter['y'],delta=1)
  self.assertLessEqual(finalFooter['y']+finalFooter['height'],1000)
 def test_embedded_recipe_does_not_move_outer_page(self):
  page,errors,_=self.page(390,embedded=True);root=page.locator('[data-editorial-web]');root.evaluate('e=>e.scrollTop=250');page.wait_for_timeout(100)
  self.assertEqual(page.evaluate('scrollY'),0)
  self.assertGreater(root.evaluate('e=>e.scrollTop'),0)
  self.assertTrue(root.evaluate('e=>e.classList.contains("web-nav-oculta")'))
  page.evaluate('NotaPiezasEditoriales.get(document.querySelector("[data-editorial-web]")).destroy()')
  self.assertFalse(root.evaluate('e=>e.classList.contains("web-nav-oculta")'))
  self.assertEqual(errors,[])
 def test_reduced_motion_print_and_noscript(self):
  page,errors,_=self.page(390,motion='reduce');page.evaluate('scrollTo({top:200,behavior:"instant"})');page.wait_for_timeout(100)
  self.assertFalse(page.locator('body').evaluate('e=>e.classList.contains("web-nav-oculta")'))
  self.assertEqual(page.locator('.web-navegacion').evaluate('e=>getComputedStyle(e).transitionDuration'),'0s')
  page.emulate_media(media='print');self.assertFalse(page.locator('.web-navegacion').is_visible());self.assertTrue(page.locator('.web-pie').is_visible());self.assertEqual(errors,[])
  page,_,requests=self.page(390,js=False);self.assertTrue(page.locator('.web-navegacion a').first.is_visible());self.assertTrue(page.locator('#web-proyectos').is_visible());self.assertEqual(requests,[])

if __name__=='__main__':unittest.main()
