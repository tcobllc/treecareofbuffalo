/* Tree Care of Buffalo, shared behavior for all pages (v1-revamp) */
(function(){
  'use strict';
  var d=document;
  window.dataLayer=window.dataLayer||[];
  function track(ev,extra){var o={event:ev};if(extra)for(var k in extra)o[k]=extra[k];window.dataLayer.push(o);}

  /* ---------- reveals: hardened. First-viewport content shows immediately;
     IntersectionObserver does the rest; a scroll/resize sweep plus a
     self-stopping interval back it up for embedders that drop IO events. ---------- */
  var reduce=window.matchMedia('(prefers-reduced-motion: reduce)');
  var rvEls=[].slice.call(d.querySelectorAll('.reveal'));
  function reveal(el){
    el.classList.add('in');
    setTimeout(function(){el.classList.add('done')},1600);
  }
  if(rvEls.length&&'IntersectionObserver' in window&&!reduce.matches&&!navigator.webdriver){
    var pending=[];
    var vh=window.innerHeight;
    var tops=rvEls.map(function(el){return el.getBoundingClientRect().top});
    rvEls.forEach(function(el,i){
      if(tops[i]<vh)reveal(el);
      else pending.push(el);
    });
    var io=new IntersectionObserver(function(entries){
      entries.forEach(function(en){
        if(!en.isIntersecting)return;
        reveal(en.target);
        io.unobserve(en.target);
        pending=pending.filter(function(el){return el!==en.target});
      });
    },{threshold:0.15});
    pending.forEach(function(el){io.observe(el)});
    var sweeping=false;
    function sweep(){
      sweeping=false;
      if(!pending.length)return;
      var h=window.innerHeight;
      pending=pending.filter(function(el){
        if(el.getBoundingClientRect().top<h){reveal(el);io.unobserve(el);return false}
        return true;
      });
    }
    window.addEventListener('scroll',function(){if(!sweeping){sweeping=true;requestAnimationFrame(sweep)}},{passive:true});
    window.addEventListener('resize',function(){if(!sweeping){sweeping=true;requestAnimationFrame(sweep)}},{passive:true});
    var tick=setInterval(function(){
      if(!pending.length){clearInterval(tick);return}
      sweep();
    },1200);
  }else{
    rvEls.forEach(function(el){el.classList.add('in','done')});
  }

  /* kerf dividers draw on approach */
  var kerfs=d.querySelectorAll('.kerf');
  if(kerfs.length&&'IntersectionObserver' in window&&!reduce.matches){
    var iok=new IntersectionObserver(function(es){
      es.forEach(function(en){if(en.isIntersecting){en.target.classList.add('in');iok.unobserve(en.target)}});
    },{threshold:0.6});
    kerfs.forEach(function(el){iok.observe(el)});
  }else{
    kerfs.forEach(function(el){el.classList.add('in')});
  }

  document.addEventListener('visibilitychange',function(){
    document.body.classList.toggle('paused',document.hidden);
  });

  /* ---------- quick-contact popup: an honest call-back panel, no fake chat presence ---------- */
  (function(){
    var fab=d.createElement('button');
    fab.className='qc-fab';
    fab.type='button';
    fab.setAttribute('aria-expanded','false');
    fab.setAttribute('aria-controls','qcPanel');
    fab.setAttribute('aria-label','Quick contact');
    fab.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 8.9 8.9 0 0 1-3.9-.9L3 20l1-4.9a8.4 8.4 0 1 1 17-3.6Z" stroke-linejoin="round"/><path d="M8 10.5h8M8 14h5" stroke-linecap="round"/></svg>';
    var panel=d.createElement('div');
    panel.id='qcPanel';
    panel.className='qc-panel';
    panel.setAttribute('role','dialog');
    panel.setAttribute('aria-label','Quick contact');
    panel.innerHTML=
      '<div class="qc-head"><img src="/assets/logo.png" alt="" width="38" height="38">'+
      '<div><b>TREE CARE OF BUFFALO</b><span>The fast lane to the crew</span></div>'+
      '<button class="qc-close" type="button" aria-label="Close">×</button></div>'+
      '<div class="qc-body">'+
      '<p class="qc-bubble">Storm damage? Skip the typing and call. For everything else, leave a call-back number and we’ll ring you back within one business day.</p>'+
      '<a class="qc-call" href="tel:+17166018275"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.4 2.1L8.1 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.6 2Z"/></svg>Call (716) 601-8275</a>'+
      '<div class="qc-or">OR HAVE US CALL YOU</div>'+
      '<form class="qc-form" novalidate>'+
      '<label>CALL-BACK NUMBER<input type="tel" name="phone" autocomplete="tel" placeholder="(716) 555-0123" required></label>'+
      '<label>WHAT DO YOU NEED DONE?<textarea name="details" placeholder="Removal, trimming, stump work, storm cleanup, a leaning tree..."></textarea></label>'+
      '<button class="qc-send" type="submit">Have us call you</button>'+
      '</form>'+
      '<div class="qc-ok" role="status"></div>'+
      '<p class="qc-foot">Want to pick a service and say more? <a href="/estimate/">The estimate page</a></p>'+
      '</div>';
    d.body.appendChild(fab);
    d.body.appendChild(panel);
    function setOpen(open){
      panel.classList.toggle('open',open);
      fab.setAttribute('aria-expanded',open?'true':'false');
      if(open)panel.querySelector('.qc-close').focus();
      else fab.focus();
    }
    fab.addEventListener('click',function(){setOpen(!panel.classList.contains('open'))});
    panel.querySelector('.qc-close').addEventListener('click',function(){setOpen(false)});
    d.addEventListener('keydown',function(e){
      if(e.key==='Escape'&&panel.classList.contains('open'))setOpen(false);
    });
    panel.querySelector('.qc-form').addEventListener('submit',function(e){
      e.preventDefault();
      var f=new FormData(this);
      var phone=(f.get('phone')||'').trim();
      var ok=panel.querySelector('.qc-ok');
      if(phone.replace(/\D/g,'').length<7){
        ok.textContent='Add a call-back number first, or just call (716) 601-8275.';
        ok.style.display='block';
        this.querySelector('input[name="phone"]').focus();
        return;
      }
      ok.style.display='';
      var body=encodeURIComponent('Please call me back.\nPhone: '+phone+'\n\nAbout the tree:\n'+(f.get('details')||''));
      /* TEMPORARY compose target until business@ receives (Workspace, ~Sep 4) */
      location.href='mailto:akimbochop13@gmail.com?subject='+encodeURIComponent('Call-back request from the website')+'&body='+body;
      panel.classList.add('sent');
      ok.textContent="Your email app should have opened. Send that and we'll call you back within one business day. In a hurry? (716) 601-8275.";
      track('form_submit',{source:'quick_contact'});
    });
  })();

  /* ---------- small-screen menu: focus trapped, focus restored ---------- */
  (function(){
    var head=d.querySelector('header');
    var nav=head&&head.querySelector('nav');
    var hidden=nav?nav.querySelectorAll('a.hideable'):[];
    if(!(head&&nav&&hidden.length))return;
    var btn=d.createElement('button');
    btn.className='menu-btn';
    btn.type='button';
    btn.setAttribute('aria-expanded','false');
    btn.setAttribute('aria-controls','mobilePanel');
    btn.textContent='MENU';
    nav.insertBefore(btn,nav.querySelector('.nav-cta'));
    var panel=d.createElement('div');
    panel.id='mobilePanel';
    panel.className='mobile-panel';
    hidden.forEach(function(a){panel.appendChild(a.cloneNode(true))});
    head.appendChild(panel);
    var opener=null;
    function trap(e){
      if(e.key==='Escape'){setOpen(false);return}
      if(e.key!=='Tab')return;
      var items=[btn].concat([].slice.call(panel.querySelectorAll('a')));
      var first=items[0],last=items[items.length-1];
      if(e.shiftKey&&d.activeElement===first){e.preventDefault();last.focus()}
      else if(!e.shiftKey&&d.activeElement===last){e.preventDefault();first.focus()}
    }
    function setOpen(open){
      head.classList.toggle('open',open);
      btn.setAttribute('aria-expanded',open?'true':'false');
      btn.textContent=open?'CLOSE':'MENU';
      if(open){
        opener=d.activeElement;
        d.addEventListener('keydown',trap);
        var firstLink=panel.querySelector('a');
        if(firstLink)firstLink.focus();
      }else{
        d.removeEventListener('keydown',trap);
        if(opener&&opener.focus)opener.focus();
        opener=null;
      }
    }
    btn.addEventListener('click',function(){setOpen(!head.classList.contains('open'))});
    panel.addEventListener('click',function(e){if(e.target.tagName==='A')setOpen(false)});
  })();

  /* ---------- sticky mobile call bar after 40 percent depth ---------- */
  (function(){
    var bar=d.createElement('div');
    bar.className='sticky-bar';
    var onEstimate=location.pathname.indexOf('/estimate')===0;
    bar.innerHTML=
      '<a class="bar-call" href="tel:+17166018275"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg> (716) 601-8275</a>'+
      '<a class="bar-est" href="'+(onEstimate?'#request':'/estimate/')+'">Free estimate</a>';
    d.body.appendChild(bar);
    var shown=false;
    function onScrollBar(){
      var max=d.documentElement.scrollHeight-window.innerHeight;
      var deep=max>0&&window.scrollY/max>0.4;
      if(deep!==shown){bar.classList.toggle('show',deep);shown=deep}
    }
    window.addEventListener('scroll',onScrollBar,{passive:true});
    bar.querySelectorAll('a').forEach(function(a){
      a.addEventListener('click',function(){
        track('sticky_bar_tap',{target:a.className.indexOf('bar-call')>-1?'call':'estimate'});
      });
    });
  })();

  /* ---------- tel link tracking ---------- */
  d.querySelectorAll('a[href^="tel:"]').forEach(function(a){
    a.addEventListener('click',function(){track('tel_click')});
  });

  /* ---------- estimate form (hardened: reserved error rows, honeypot only,
     honest mailto, success state focused) ---------- */
  var form=d.querySelector('form.quote-form:not(.qc-form)');
  if(form){
    var fields={
      name:{test:function(v){return v.trim().length>=2},msg:'Enter your name.'},
      phone:{test:function(v){return v.replace(/\D/g,'').length>=10},msg:'Enter a phone number with area code.'},
      address:{test:function(v){return v.trim().length>=3},msg:'Enter an address or the nearest cross street.'},
      details:{test:function(v){return v.trim().length>=10},msg:'Tell us a little about the tree so the estimate is accurate.'}
    };
    function validateField(input){
      var rule=fields[input.name];
      if(!rule)return true;
      var ok=rule.test(input.value);
      var wrap=input.closest('.field');
      wrap.classList.toggle('invalid',!ok);
      var err=wrap.querySelector('.err');
      if(err){err.textContent=ok?'':rule.msg}
      input.setAttribute('aria-invalid',ok?'false':'true');
      return ok;
    }
    form.querySelectorAll('input[name], textarea[name]').forEach(function(input){
      input.addEventListener('blur',function(){if(input.value!=='')validateField(input)});
    });
    var urgent=form.querySelector('input[name="urgent"]');
    var submitBtn=form.querySelector('button[type="submit"]');
    var urgentNote=form.querySelector('.urgent-note');
    if(urgent){
      urgent.addEventListener('change',function(){
        submitBtn.textContent=urgent.checked?'Send urgent request':submitBtn.getAttribute('data-label');
        if(urgentNote)urgentNote.classList.toggle('show',urgent.checked);
      });
    }
    form.addEventListener('submit',function(e){
      e.preventDefault();
      /* spam gate: honeypot only. CONTACT STEP: when a real form endpoint replaces
         mailto, add server-side spam protection there, never client-side gates
         that can eat real clicks. */
      /* the trap field has a nonsense name so browser autofill never fills it
         and silently eats a real submission */
      var trap=form.querySelector('input[name="tcob-trap"]');
      if(trap&&trap.value!=='')return;
      var allOk=true,firstBad=null;
      form.querySelectorAll('input[name], textarea[name]').forEach(function(input){
        if(fields[input.name]&&!validateField(input)){
          allOk=false;
          if(!firstBad)firstBad=input;
        }
      });
      if(!allOk){firstBad.focus();return}
      var v=function(n){return form.querySelector('[name="'+n+'"]').value.trim()};
      var isUrgent=urgent&&urgent.checked;
      var okBox=form.parentElement.querySelector('.form-success');
      function finish(direct){
        if(direct&&okBox){
          var h=okBox.querySelector('h3'),p=okBox.querySelector('p');
          if(h)h.textContent='Request sent.';
          if(p)p.textContent='It landed with us directly. We answer within one business day, sooner for storm calls. Photos help: text them to (716) 601-8275 with your name.';
        }
        form.style.display='none';
        if(okBox){okBox.classList.add('show');okBox.focus()}
      }
      function mailtoSend(){
        var body=[
          (isUrgent?'URGENT / STORM DAMAGE':'Estimate request'),
          '',
          'Name: '+v('name'),
          'Phone: '+v('phone'),
          'Address / cross street: '+v('address'),
          '',
          'What is going on:',
          v('details'),
          '',
          '(If you have photos of the tree, attach them to this email before sending.)'
        ].join('\n');
        var subject=(isUrgent?'URGENT tree work request':'Free estimate request')+' from '+v('name');
        /* TEMPORARY compose target until business@ receives (Workspace, ~Sep 4) */
        window.location.href='mailto:akimbochop13@gmail.com?subject='+
          encodeURIComponent(subject)+'&body='+encodeURIComponent(body);
        track('form_submit',{urgent:!!isUrgent,path:'mailto'});
        finish(false);
      }
      /* try the real endpoint first (Turnstile-protected Pages Function); fall back
         to the honest mailto on any failure, so the form can never dead-end */
      var ENDPOINT=/\.pages\.dev$/.test(location.hostname)?'/api/lead':'https://treecareofbuffalo.pages.dev/api/lead';
      var fd;
      try{fd=new FormData(form)}catch(err){mailtoSend();return}
      var photoInput=form.querySelector('input[name="photos"]');
      fd.delete('photos');
      fd.append('photos-count',String(photoInput&&photoInput.files?photoInput.files.length:0));
      var ctrl=('AbortController' in window)?new AbortController():null;
      var timer=ctrl?setTimeout(function(){ctrl.abort()},8000):null;
      fetch(ENDPOINT,{method:'POST',body:fd,signal:ctrl?ctrl.signal:undefined})
        .then(function(r){
          if(timer)clearTimeout(timer);
          if(r.ok){track('form_submit',{urgent:!!isUrgent,path:'endpoint'});finish(true)}
          else{mailtoSend()}
        })
        .catch(function(){if(timer)clearTimeout(timer);mailtoSend()});
    });
  }

  /* ---------- ambient video backgrounds: desktop, motion-ok, data-ok only ---------- */
  (function(){
    var els=d.querySelectorAll('[data-ambient]');
    if(!els.length||reduce.matches)return;
    if(navigator.connection&&navigator.connection.saveData)return;
    if(!matchMedia('(min-width:861px)').matches)return;
    Array.prototype.forEach.call(els,function(el){
      var v=d.createElement('video');
      v.muted=true;v.loop=true;v.autoplay=true;v.playsInline=true;
      v.setAttribute('muted','');v.setAttribute('playsinline','');v.setAttribute('aria-hidden','true');
      v.src=el.getAttribute('data-ambient');
      el.appendChild(v);
      el.classList.add('hasvid');
      var p=v.play();
      if(p&&p.catch)p.catch(function(){v.remove();el.classList.remove('hasvid')});
    });
  })();
})();
