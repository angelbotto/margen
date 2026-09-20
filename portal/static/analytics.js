/* Optional owner-enabled analytics. Only the trusted reader shell sends page opens. */
window.MargenAnalytics = {
  async visit(api, artifact, user, version) {
    if (user?.id === artifact.owner || version !== artifact.current_version || navigator.doNotTrack === '1' || navigator.globalPrivacyControl || window.top !== window.self) return;
    const config = await api('/api/artifacts/' + artifact.id + '/analytics-config');
    if (!config.enabled) return;
    await api('/api/artifacts/' + artifact.id + '/visit', {method:'POST', body:'{}'});
    if (!config.umami) return;
    const script = document.createElement('script');
    script.src = config.umami.origin + '/script.js';
    script.dataset.websiteId = config.umami.website;
    script.dataset.autoTrack = 'false';
    script.dataset.doNotTrack = 'true';
    script.dataset.excludeSearch = 'true';
    script.dataset.excludeHash = 'true';
    script.onload = () => window.umami?.track({website:config.umami.website,hostname:location.hostname,url:'/a/'+artifact.id,title:'Margen artifact',referrer:'',language:navigator.language,screen:screen.width+'x'+screen.height});
    document.head.append(script);
  }
};
