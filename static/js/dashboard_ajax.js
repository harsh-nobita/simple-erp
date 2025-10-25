// Dashboard AJAX loader: intercept sidebar clicks pointing to /dashboard and load content via fetch.
// Replaces inner HTML of #main-content-area with the server-rendered fragment.

(function(){
    function isDashboardLink(anchor){
        try{
            var url = new URL(anchor.href, window.location.origin);
            return url.pathname === '/' || url.pathname.endsWith('/dashboard');
        }catch(e){
            return false;
        }
    }

    function setActiveSidebar(href){
        var sidebarLinks = document.querySelectorAll('nav.sidebar a.nav-link');
        sidebarLinks.forEach(function(link){
            link.classList.remove('active');
            // if link href equals href (ignoring origin)
            try{
                var linkUrl = new URL(link.href, window.location.origin);
                var targetUrl = new URL(href, window.location.origin);
                if(linkUrl.pathname === targetUrl.pathname && linkUrl.search === targetUrl.search){
                    link.classList.add('active');
                }
            }catch(e){}
        });
    }

    async function loadDashboardFragment(href, addToHistory){
        try{
            var resp = await fetch(href, {headers: {'X-Requested-With': 'XMLHttpRequest'}});
            if(!resp.ok){
                // fallback to full navigation
                window.location.href = href;
                return;
            }
            var html = await resp.text();
            var container = document.getElementById('main-content-area');
            if(container){
                container.innerHTML = html;
                // update active class on sidebar
                setActiveSidebar(href);
                if(addToHistory){
                    history.pushState({ajax: true, href: href}, '', href);
                }
                // re-run any module-specific init if present
                if(window.moduleInit && typeof window.moduleInit === 'function'){
                    try{ window.moduleInit(); }catch(e){}
                }
            } else {
                // no container found, fallback
                window.location.href = href;
            }
        }catch(e){
            console.error('AJAX load failed, falling back to full navigation', e);
            window.location.href = href;
        }
    }

    document.addEventListener('click', function(e){
        var target = e.target;
        // find closest anchor
        while(target && target.tagName !== 'A') target = target.parentElement;
        if(!target) return;
        if(!isDashboardLink(target)) return; // only intercept dashboard links

        // intercept
        e.preventDefault();
        var href = target.href;
        loadDashboardFragment(href, true);
    }, true);

    // handle back/forward
    window.addEventListener('popstate', function(e){
        var href = location.href;
        // when navigating back to dashboard-like paths, load fragment
        if(location.pathname === '/' || location.pathname.endsWith('/dashboard')){
            loadDashboardFragment(href, false);
        } else {
            // allow normal navigation
            window.location.href = href;
        }
    });

    // Expose a small helper to load programmatically
    window.loadDashboardSection = function(section){
        var href = section ? (window.location.origin + '/dashboard?section=' + encodeURIComponent(section)) : (window.location.origin + '/dashboard');
        loadDashboardFragment(href, true);
    };
})();
