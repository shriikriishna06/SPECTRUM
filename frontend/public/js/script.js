const API_BASE = "https://spectrumx.duckdns.org";

function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function buildRecommendationCardHtml(item, opts) {
  const compact = opts && opts.compact === true;
  const whyText = Array.isArray(item.why_recommended) ? item.why_recommended.join(" • ") : item.why_recommended;
  const tmdbLink = item.tmdb_link;
  const title = escapeHtml(item.title || "Untitled");

  let platformsBlock = "";
  if (item.watch_on && item.watch_on.length > 0) {
    const inner = item.watch_on.map(p => `<img src="https://image.tmdb.org/t/p/original${p.logo}" alt="${p.platform}" class="h-6 rounded" title="${p.platform}">`).join('');
    platformsBlock = `<div class="flex gap-2 items-center flex-wrap pt-2">${inner}</div>`;
  } else if (!compact) {
    platformsBlock = `<div class="flex gap-2 items-center flex-wrap pt-2"><span class="text-xs text-gray-500">Not available</span></div>`;
  }

  const whyBlock = compact
    ? ""
    : `<p class="text-xs text-gray-300 border-t border-white/10 pt-2 leading-relaxed line-clamp-3">${whyText}</p>`;

  const cardPad = compact ? "p-3 sm:p-4" : "p-5";
  const cardMin = compact ? "min-h-0" : "min-h-[520px]";
  const titleCls = compact ? "text-sm sm:text-base" : "text-base";
  const metaCls = compact ? "text-[10px] sm:text-xs" : "text-xs";
  const btnCls = compact ? "mt-3 py-2 text-[10px] sm:text-xs" : "mt-4 py-2 text-xs";

  return `
      <div class="glass-panel ${cardPad} rounded-2xl hover:bg-white/5 transition-all group flex flex-col justify-between h-full ${cardMin}">
        <div class="flex flex-col gap-2 sm:gap-3 flex-1">
          <div class="relative w-full aspect-[2/3] rounded-xl overflow-hidden">
            <img src="https://image.tmdb.org/t/p/w500${item.poster || ''}" 
                 class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" 
                 alt="${title}"
                 onerror="this.src='https://placehold.co/500x750/000000/FFFFFF?text=No+Image'">
          </div>
          <div class="flex flex-col gap-1.5 sm:gap-2 flex-1">
            <h3 class="${titleCls} font-bold text-white group-hover:text-brandCyan transition-colors line-clamp-2">${title}</h3>
            <p class="${metaCls} text-gray-400 uppercase tracking-wide">${(item.language || "—").toUpperCase()} • ${item.type || "Movie"}</p>
            ${whyBlock}
            ${platformsBlock}
          </div>
        </div>
        <a href="${tmdbLink}" target="_blank" rel="noopener noreferrer" class="block w-full ${btnCls} text-center rounded-lg bg-white/5 hover:bg-brandCyan hover:text-black transition-colors font-bold uppercase tracking-wider">View Details</a>
      </div>
    `;
}

//results card 
function renderResults(list) {
  const container = document.getElementById("results-grid");
  if (!container) return;
  container.innerHTML = "";

  if (!list || list.length === 0) {
    container.innerHTML = "<p class='text-gray-400'>No recommendations found.</p>";
    return;
  }

  list.forEach(item => {
    container.innerHTML += buildRecommendationCardHtml(item);
  });
}

// popular page rendering
const DEFAULT_POPULAR_LANG = "en";
let popularActiveLang = DEFAULT_POPULAR_LANG;
let popularRequestId = 0;
let popularAbortController = null;

function normalizePopularLang(lang) {
  const code = lang != null ? String(lang).trim().toLowerCase() : "";
  return code || DEFAULT_POPULAR_LANG;
}

function updatePopularLangPills(langCode) {
  const bar = document.getElementById("popular-lang-bar");
  if (!bar) return;
  bar.querySelectorAll("[data-lang]").forEach((btn) => {
    const selected = btn.getAttribute("data-lang") === langCode;
    btn.classList.toggle("selected", selected);
    btn.setAttribute("aria-pressed", String(selected));
  });
}

function updatePopularNavState(isActive) {
  document.body.classList.toggle("popular-route-active", isActive);

  const popularLink = document.getElementById("popular-nav-link");
  if (popularLink) {
    popularLink.classList.toggle("text-white", isActive);
    popularLink.classList.toggle("text-gray-400", !isActive);
    if (isActive) {
      popularLink.setAttribute("aria-current", "page");
    } else {
      popularLink.removeAttribute("aria-current");
    }
  }
}

function selectPopularLanguage(langCode) {
  navigateToPopular(langCode);
}

function renderPopular(apiData) {
  const root = document.getElementById("popular-genres-root");
  if (!root) return;
  root.innerHTML = "";

  const genres = apiData.genres || [];
  if (genres.length === 0) {
    root.innerHTML = "<p class='text-gray-400 text-sm px-1'>No popular titles found for this language.</p>";
    return;
  }

  let anySection = false;
  let genreRowIndex = 0;
  genres.forEach((g) => {
    const raw = g.movies || [];
    if (raw.length === 0) return;

    const movies = raw.map((m) => ({
      ...m,
      type: "Movie",
      watch_on: [],
    }));

    const cardsHtml = movies
      .map(
        (m) =>
          `<div class="popular-marquee-card w-[138px] sm:w-[172px] md:w-[198px]">` +
          buildRecommendationCardHtml(m, { compact: true }) +
          "</div>"
      )
      .join("");

    const durationSec = Math.min(110, Math.max(50, movies.length * 3.4));
    const revClass = genreRowIndex % 2 === 1 ? " popular-marquee-track--rev" : "";

    const section = document.createElement("section");
    section.className = "w-full";
    section.innerHTML = `
      <div class="mb-3 sm:mb-4">
        <h3 class="text-lg sm:text-xl md:text-2xl font-bold tracking-tight text-white">
          <span class="text-violet-400">${escapeHtml(g.name)}</span>
        </h3>
        <p class="text-[10px] sm:text-xs text-gray-500 uppercase tracking-wider mt-1">${movies.length} titles</p>
      </div>
      <div class="popular-marquee-outer py-1 sm:py-2 -mx-0.5 sm:mx-0">
        <div class="popular-marquee-track${revClass}" style="animation-duration: ${durationSec}s">
          <div class="popular-marquee-segment">${cardsHtml}</div>
          <div class="popular-marquee-segment" aria-hidden="true">${cardsHtml}</div>
        </div>
      </div>
    `;

    root.appendChild(section);
    anySection = true;
    genreRowIndex += 1;
  });

  if (!anySection) {
    root.innerHTML = "<p class='text-gray-400 text-sm px-1'>No popular titles found for this language.</p>";
  }
}

let popularWheelListenerAttached = false;

function ensurePopularGlobalWheelScroll() {
  if (popularWheelListenerAttached) return;
  popularWheelListenerAttached = true;
  window.addEventListener(
    "wheel",
    function onPopularGlobalWheel(e) {
      const wrap = document.getElementById("popular-results-wrap");
      if (!wrap || wrap.classList.contains("hidden") || !wrap.classList.contains("popular-view-active")) {
        return;
      }
      if (Math.abs(e.deltaY) < Math.abs(e.deltaX)) {
        return;
      }
      window.scrollBy(0, e.deltaY);
      e.preventDefault();
    },
    { passive: false, capture: true }
  );
}

function showPopularPage() {
  ensurePopularGlobalWheelScroll();
  updatePopularNavState(true);
  document.getElementById("landing-hero-view")?.classList.add("hidden");
  const wrap = document.getElementById("popular-results-wrap");
  if (wrap) {
    wrap.classList.remove("hidden");
    wrap.classList.add("popular-view-active");
  }
  window.scrollTo(0, 0);
}

function closePopularPageView(options) {
  const fromRoute = options && options.fromRoute === true;
  if (!fromRoute) {
    updateHomeRoute();
  }

  updatePopularNavState(false);
  popularRequestId += 1;
  if (popularAbortController) {
    popularAbortController.abort();
    popularAbortController = null;
  }
  setLoading(false);
  document.getElementById("landing-hero-view")?.classList.remove("hidden");
  const wrap = document.getElementById("popular-results-wrap");
  if (wrap) {
    wrap.classList.add("hidden");
    wrap.classList.remove("popular-view-active");
    wrap.removeAttribute("aria-busy");
  }
  window.scrollTo(0, 0);
}

//apis
async function startWatching() {
  let id = localStorage.getItem("user_id");

  if (id) {
    id = id.trim();
    if (!id) {
      localStorage.removeItem("user_id");
      localStorage.removeItem("onboarded");
    } else {
      try {
        const res = await fetch(
          `${API_BASE}/init/exists/${encodeURIComponent(id)}`
        );
        if (!res.ok) {
          const errText = await res.text();
          console.error("exists check failed:", res.status, errText);
          alert(
            "Could not verify your account with the server."
          );
          return;
        }
        const data = await res.json();
        if (data.exists === true) {
          window.location.href = "session.html";
          return;
        }
        localStorage.removeItem("user_id");
        localStorage.removeItem("onboarded");
      } catch (e) {
        console.error("Backend check failed", e);
        alert(
          "Network error while verifying your account."
        );
        return;
      }
    }
  }

  try {
    const res = await fetch(`${API_BASE}/init/`, { method: "POST" });
    const data = await res.json();

    localStorage.setItem("user_id", data.user_id);
    localStorage.setItem("onboarded", "false");

    window.location.href = "app.html";
  } catch (e) {
    alert("Network error: Cannot connect to the server.");
  }
}

async function submitOnboarding() {
  const userId = localStorage.getItem("user_id");
  if (!userId) {
    alert("User not initialized");
    return;
  }

  const age = document.querySelector("#q-age .selected")?.dataset.value || "adult";
  const mood = document.querySelector("#q-vibe .selected")?.dataset.value || "balanced";
  const runtime = document.querySelector("#q-runtime .selected")?.dataset.value || "any";
  const risk = document.querySelector("#q-risk .selected")?.dataset.value || "low";

  const genres = [...document.querySelectorAll("#q-genres .selected")]
    .map(el => el.dataset.value);

  const languages = [...document.querySelectorAll("#q-lang .selected")]
    .map(el => el.dataset.value)
    .join(",");

  const payload = {
    user_id: userId,
    age_group: age,
    genres: genres,
    mood: mood,
    language: languages,
    runtime_pref: runtime,
    risk: risk
  };

  try {
    const res = await fetch(`${API_BASE}/questionnaire/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.text();
      console.error(err);
      alert("Failed to save preferences");
      return;
    }

    localStorage.setItem("onboarded", "true");

  } catch (e) {
    console.error(e);
    alert("Network error");
  }
}

async function submitSession() {
  const userId = localStorage.getItem("user_id");
  if (!userId) {
    alert("User not initialized");
    return;
  }

  const typedMood = document.getElementById("s-mood-input")?.value.trim();
  const presetMoodEl = document.querySelector("#s-mood-presets .selected");

  let mood = "";
  if (typedMood && typedMood.length >= 3) {
    mood = typedMood;
  } else if (presetMoodEl) {
    mood = presetMoodEl.innerText.toLowerCase();
  }
  const langEl = document.querySelector("#s-lang .selected");
  const languageMode = langEl?.dataset.value || "any";

  if (!mood && !langEl) {
    alert("Please provide a mood and select a language.");
    return;
  }

  if (!mood) {
    alert("Select or type a mood.");
    return;
  }

  if (!langEl) {
    alert("Please select a language.");
    return;
  }
  const payload = {
    user_id: userId,
    session: {
      mood: mood,
      language_mode: languageMode
    }
  };

  const btnText = document.getElementById("btn-text");
  const loader = document.getElementById("btn-loader");

  if (btnText) btnText.innerText = "Getting recommendations...";
  if (loader) loader.classList.remove("hidden");

  try {
    const res = await fetch(`${API_BASE}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errBody = await res.text();
      throw new Error(`Recommendation failed.Try again later...`);
    }

    const data = await res.json();

    if (data.recommendations && data.recommendations.length > 0) {
      renderResults(data.recommendations);
      showView("view-results");
    } else {
      alert("No recommendations found. Try different preferences.");
    }

  } catch (err) {
    console.error(err);
    alert("Failed to get recommendations: " + err.message);
  } finally {
    if (btnText) btnText.innerText = "Get recommendations";
    if (loader) loader.classList.add("hidden");
  }
}

async function resetPreferences() {
  if (confirm("Are you sure you want to reset your preferences? You will need to set up your profile again.")) {
    const userId = localStorage.getItem("user_id");
    if (userId) {
      try {
        const res = await fetch(`${API_BASE}/init/preferences/${encodeURIComponent(userId)}`, {
          method: 'DELETE'
        });
        if (!res.ok) {
          alert("Failed to reset preferences. Please try again.");
          return;
        }
      } catch (e) {
        console.error("Error resetting preferences:", e);
        alert("Error resetting preferences.");
        return;
      }
    }
    window.location.href = "app.html";
  }
}

async function popularNow(lang) {
  const code = normalizePopularLang(lang || popularActiveLang);
  const requestId = popularRequestId + 1;
  popularRequestId = requestId;
  popularActiveLang = code;

  if (popularAbortController) {
    popularAbortController.abort();
  }
  popularAbortController = new AbortController();

  showPopularPage();
  updatePopularLangPills(code);

  setLoading(true);

  try {
    const res = await fetch(`${API_BASE}/popular/?lang=${encodeURIComponent(code)}`, {
      signal: popularAbortController.signal,
    });

    if (!res.ok) {
      throw new Error("Failed to fetch popular movies");
    }

    const data = await res.json();

    if (requestId !== popularRequestId) return;

    renderPopular(data);

  } catch (err) {
    if (err.name === "AbortError") return;
    console.error(err);
    renderPopularMessage("Could not load popular titles. Try again in a moment.");
  } finally {
    if (requestId === popularRequestId) {
      setLoading(false);
    }
  }
}

// frontend route handling
function buildCurrentRouteUrl(params) {
  const query = params.toString();
  return `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`;
}

function writeRoute(params, state, replace) {
  const nextUrl = buildCurrentRouteUrl(params);
  const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (nextUrl === currentUrl) return;

  const method = replace ? "replaceState" : "pushState";
  history[method](state, "", nextUrl);
}

function updatePopularRoute(lang, replace) {
  const code = normalizePopularLang(lang);
  const params = new URLSearchParams(window.location.search);
  params.set("category", "popular");
  params.set("lang", code);
  writeRoute(params, { view: "popular", lang: code }, replace);
}

function updateHomeRoute(replace) {
  const params = new URLSearchParams(window.location.search);
  params.delete("category");
  params.delete("lang");
  writeRoute(params, { view: "home" }, replace);
}

function navigateHome(event) {
  if (event && typeof event.preventDefault === "function") {
    event.preventDefault();
  }
  closePopularPageView({ fromRoute: true });
  updateHomeRoute();
}

function navigateToPopular(lang, options) {
  const code = normalizePopularLang(lang);
  const replace = options && options.replace === true;
  updatePopularRoute(code, replace);
  popularNow(code);
}

function renderPopularMessage(message) {
  const root = document.getElementById("popular-genres-root");
  if (!root) return;
  root.innerHTML = `<p class="text-gray-400 text-sm px-1">${escapeHtml(message)}</p>`;
}

function isPopularPath() {
  const path = window.location.pathname.replace(/\/+$/, "").toLowerCase();
  return path.endsWith("/movies") || path.endsWith("/popular");
}


function handlePopularClick(eventOrLang, maybeLang) {
  if (eventOrLang && typeof eventOrLang.preventDefault === "function") {
    eventOrLang.preventDefault();
    navigateToPopular(maybeLang || DEFAULT_POPULAR_LANG);
    return;
  }

  navigateToPopular(eventOrLang || maybeLang || popularActiveLang || DEFAULT_POPULAR_LANG);
}

function handleRouteChange() {
  const params = new URLSearchParams(window.location.search);
  const category = params.get("category");
  const lang = normalizePopularLang(params.get("lang"));

  if (category === "popular" || isPopularPath()) {
    popularNow(lang);
    return;
  }

  closePopularPageView({ fromRoute: true });
}
window.addEventListener("popstate", handleRouteChange);

function setLoading(isLoading) {
  document.body.classList.toggle("popular-loading", isLoading);

  const wrap = document.getElementById("popular-results-wrap");
  if (wrap) {
    wrap.setAttribute("aria-busy", String(isLoading));
  }
}

window.addEventListener("load", handleRouteChange);
