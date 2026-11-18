// ascii_world foundation. No dependencies, no build.
// Each block below is independent: delete one and the rest still works.

const world = { actions: {} };
const calm = matchMedia('(prefers-reduced-motion: reduce)').matches;

// ---------- click ----------
// <pre class="thing" data-click="bloom"> runs world.actions.bloom(element, event).
// Define actions in the page: world.actions.bloom = el => { ... }
document.addEventListener('click', e => {
    const el = e.target.closest('[data-click]');
    if (!el) return;
    const action = world.actions[el.dataset.click];
    if (action) action(el, e);
    else console.warn(`no action named "${el.dataset.click}"`);
});

// ---------- frames ----------
// world.next(el) shows the next frame; usable from actions too.
world.next = el => {
    const frames = [...el.children];
    const i = frames.findIndex(f => f.classList.contains('on'));
    frames[i]?.classList.remove('on');
    frames[(i + 1) % frames.length].classList.add('on');
};

for (const el of document.querySelectorAll('.frames')) {
    el.firstElementChild.classList.add('on');
    const play = el.dataset.play || 'always';
    const ms = 1000 / (el.dataset.fps || 4);
    let timer = null;
    const start = () => { timer ??= setInterval(() => world.next(el), ms); };
    const stop = () => { clearInterval(timer); timer = null; };
    if (play === 'always' && !calm) start();
    if (play === 'hover') {
        el.addEventListener('pointerenter', start);
        el.addEventListener('pointerleave', stop);
    }
}

// ---------- image strips ----------
// Gives each image strip its height in units (--h) from its own proportions, so
// the phone stretch in world.css can make it taller. An --h you set yourself wins.
const designWidth = +getComputedStyle(document.documentElement).getPropertyValue('--design-width');
for (const img of document.querySelectorAll('img.strip')) {
    if (img.style.getPropertyValue('--h')) continue;
    const set = (w, h) => { if (w && h) img.style.setProperty('--h', h / w * designWidth); };
    const w = +img.getAttribute('width'), h = +img.getAttribute('height');
    if (w && h) set(w, h);
    else if (img.complete) set(img.naturalWidth, img.naturalHeight);
    else img.addEventListener('load', () => set(img.naturalWidth, img.naturalHeight), { once: true });
}

// ---------- reveal ----------
// data-reveal: gets the class "in-view" while on screen. The look is in world.css.
const watcher = new IntersectionObserver(entries => {
    for (const entry of entries) entry.target.classList.toggle('in-view', entry.isIntersecting);
}, { threshold: 0.2 });
for (const el of document.querySelectorAll('[data-reveal]')) watcher.observe(el);

// ---------- parallax ----------
// data-parallax="0.3": lags behind the scroll by 30% (feels further away).
// Negative values move faster (feels closer). The element sits exactly at its
// placed position when it is in the vertical middle of the screen.
// Where the browser supports it, world.css runs this as a scroll-driven
// animation, which stays smooth on phones; the code below is only the fallback.
const movers = [...document.querySelectorAll('[data-parallax]')];
for (const el of movers) el.style.setProperty('--parallax', el.dataset.parallax);
if (movers.length && !calm && !CSS.supports('animation-timeline: view()')) {
    let queued = false;
    const update = () => {
        queued = false;
        const middle = scrollY + innerHeight / 2;
        for (const el of movers) {
            const home = el.offsetTop + el.offsetHeight / 2;
            el.style.translate = `0 ${(middle - home) * el.dataset.parallax}px`;
        }
    };
    const queue = () => { if (!queued) { queued = true; requestAnimationFrame(update); } };
    addEventListener('scroll', queue, { passive: true });
    addEventListener('resize', queue);
    update();
}
