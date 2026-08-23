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
