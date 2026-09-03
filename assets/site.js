/* Tree Care of Buffalo, shared behavior for all pages */
(function(){
  var io=new IntersectionObserver(function(es){
    es.forEach(function(en){
      if(en.isIntersecting){
        en.target.classList.add('in');
        setTimeout(function(){en.target.classList.add('done')},1600);
        io.unobserve(en.target);
      }
    });
  },{threshold:0.18});
  document.querySelectorAll('.reveal').forEach(function(el){io.observe(el)});

  var iok=new IntersectionObserver(function(es){
    es.forEach(function(en){
      if(en.isIntersecting){en.target.classList.add('in');iok.unobserve(en.target)}
    });
  },{threshold:0.6});
  document.querySelectorAll('.kerf').forEach(function(el){iok.observe(el)});

  document.addEventListener('visibilitychange',function(){
    document.body.classList.toggle('paused',document.hidden);
  });

  /* quick-contact popup: an honest call-back panel, no fake chat presence */
  (function(){
    var fab=document.createElement('button');
    fab.className='qc-fab';
    fab.type='button';
    fab.setAttribute('aria-expanded','false');
    fab.setAttribute('aria-controls','qcPanel');
    fab.setAttribute('aria-label','Quick contact');
    fab.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 8.9 8.9 0 0 1-3.9-.9L3 20l1-4.9a8.4 8.4 0 1 1 17-3.6Z" stroke-linejoin="round"/><path d="M8 10.5h8M8 14h5" stroke-linecap="round"/></svg>';
    var panel=document.createElement('div');
    panel.id='qcPanel';
    panel.className='qc-panel';
    panel.setAttribute('role','dialog');
    panel.setAttribute('aria-label','Quick contact');
    panel.innerHTML=
      '<div class="qc-head"><img src="assets/logo.png" alt="" width="38" height="38">'+
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
      '<p class="qc-foot">Want to pick a service and say more? <a href="booking.html">The booking page</a></p>'+
      '</div>';
    document.body.appendChild(fab);
    document.body.appendChild(panel);
    function setOpen(open){
      panel.classList.toggle('open',open);
      fab.setAttribute('aria-expanded',open?'true':'false');
      if(open)panel.querySelector('.qc-close').focus();
      else fab.focus();
    }
    fab.addEventListener('click',function(){setOpen(!panel.classList.contains('open'))});
    panel.querySelector('.qc-close').addEventListener('click',function(){setOpen(false)});
    document.addEventListener('keydown',function(e){
      if(e.key==='Escape'&&panel.classList.contains('open'))setOpen(false);
    });
    panel.querySelector('.qc-form').addEventListener('submit',function(e){
      e.preventDefault();
      var f=new FormData(this);
      var body=encodeURIComponent('Please call me back.\nPhone: '+(f.get('phone')||'')+'\n\nAbout the tree:\n'+(f.get('details')||''));
      /* TEMPORARY compose target until business@ receives (see booking.html note) */
      location.href='mailto:akimbochop13@gmail.com?subject='+encodeURIComponent('Call-back request from the website')+'&body='+body;
      panel.classList.add('sent');
      panel.querySelector('.qc-ok').textContent="Your email app should have opened. Send that and we'll call you back within one business day. In a hurry? (716) 601-8275.";
    });
  })();

  /* small-screen menu: built from the nav links the narrow header hides */
  var head=document.querySelector('header');
  var nav=head&&head.querySelector('nav');
  var hidden=nav?nav.querySelectorAll('a.hideable'):[];
  if(head&&nav&&hidden.length){
    var btn=document.createElement('button');
    btn.className='menu-btn';
    btn.type='button';
    btn.setAttribute('aria-expanded','false');
    btn.setAttribute('aria-controls','mobilePanel');
    btn.textContent='MENU';
    nav.insertBefore(btn,nav.querySelector('.nav-cta'));
    var panel=document.createElement('div');
    panel.id='mobilePanel';
    panel.className='mobile-panel';
    hidden.forEach(function(a){panel.appendChild(a.cloneNode(true))});
    head.appendChild(panel);
    btn.addEventListener('click',function(){
      var open=head.classList.toggle('open');
      btn.setAttribute('aria-expanded',open?'true':'false');
      btn.textContent=open?'CLOSE':'MENU';
    });
  }
})();
