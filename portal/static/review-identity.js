/* Identity labels come from server fields, never from the spelling of a name. */
(() => {
  'use strict';
  const clean = value => typeof value === 'string'
    ? value.replace(/[\x00-\x1f\x7f-\x9f\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]/g, ' ').replace(/\s+/g, ' ').trim() : '';
  const name = event => {
    const author = clean(event.author) || 'Sin nombre', agent = clean(event.agent);
    return agent ? agent + ' (agente de ' + author + ')' : author;
  };
  const kind = event => clean(event.agent) ? 'conexión de agente'
    : event.verified === true ? 'correo verificado'
      : event.verified === false ? 'invitado' : 'verificación no registrada';
  const label = event => name(event) + ' · ' + kind(event);
  const fragment = event => {
    const result = document.createDocumentFragment(), person = document.createElement('bdi'), badge = document.createElement('span');
    person.textContent = name(event);
    badge.className = 'review-identity-kind';
    badge.dataset.reviewIdentityKind = clean(event.agent) ? 'agent' : event.verified === true ? 'verified' : event.verified === false ? 'guest' : 'unknown';
    badge.textContent = kind(event);
    result.append(person, document.createTextNode(' · '), badge);
    return result;
  };
  const element = (tag, event, prefix = '', suffix = '', className = '') => {
    const result = document.createElement(tag);
    if (className) result.className = className;
    result.append(document.createTextNode(prefix), fragment(event), document.createTextNode(suffix));
    return result;
  };
  window.MargenReviewIdentity = {name, kind, label, fragment, element};
})();
