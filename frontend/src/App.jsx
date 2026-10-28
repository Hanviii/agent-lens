import React from "react";
import { useMemo, useState } from "react";
import {
  Activity, ArrowDownUp, ArrowRight, AudioLines, Check,
  ChevronDown, Cpu, Headphones, Heart, Laptop, LoaderCircle,
  Search, ShieldCheck, Sparkles, SlidersHorizontal, Star,
  Watch, X, Zap
} from "lucide-react";

const API = "http" + "://127.0.0.1:8000";

const suggestions = [
  { icon: Headphones, text: "Headphones under $30" },
  { icon: Laptop, text: "Laptops for students" },
  { icon: Watch, text: "Smartwatches with great ratings" },
];

const categories = ["All products", "Audio", "Computers", "Accessories", "Wearables"];

function getCategory(product) {
  const text = `${product.title || ""} ${product.category || ""}`.toLowerCase();
  if (/headphone|earbud|earphone|speaker|audio/.test(text)) return "Audio";
  if (/laptop|computer|keyboard|monitor|mouse|tablet/.test(text)) return "Computers";
  if (/watch|fitness band/.test(text)) return "Wearables";
  if (/charger|cable|case|adapter|stand/.test(text)) return "Accessories";
  return "Other";
}

function ProductArt({ product, index }) {
  const title = (product.title || "").toLowerCase();
  const Icon = /watch|band/.test(title) ? Watch
    : /laptop|computer|monitor|keyboard/.test(title) ? Laptop
    : /speaker|radio/.test(title) ? AudioLines
    : /headphone|earbud|earphone/.test(title) ? Headphones : Cpu;

  if (product.image_url) {
    return <img className="product-image" src={product.image_url} alt={product.title} loading="lazy" onError={(e) => { e.currentTarget.style.display = "none"; }} />;
  }

  return (
    <div className={`product-art art-${index % 5}`}>
      <span className="art-glow" />
      <Icon size={76} strokeWidth={1.1} />
      <span className="art-caption">AGENTLENS SELECT</span>
    </div>
  );
}

function App() {
  const [question, setQuestion] = useState("");
  const [products, setProducts] = useState([]);
  const [activeCategory, setActiveCategory] = useState("All products");
  const [minRating, setMinRating] = useState("0");
  const [sort, setSort] = useState("relevance");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [answer, setAnswer] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [favorites, setFavorites] = useState([]);
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  async function searchProducts(value = question) {
    const q = value.trim();
    if (!q || loading) return;

    setQuestion(q);
    setLoading(true);
    setError("");
    setAnswer("");
    setHasSearched(true);
    setActiveCategory("All products");

    try {
      const response = await fetch(`${API}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.error || "The search could not be completed.");
      }

      const found = Array.isArray(data.products) ? data.products : data.results || [];
      setProducts(found);
      setAnswer(data.answer || `Found ${found.length} matching products.`);
      if (!found.length) setError("No matching products found. Try a broader search.");
    } catch (err) {
      setProducts([]);
      setError(
        err.message?.includes("fetch")
          ? "Can't reach AgentLens API. Make sure your backend is running at 127.0.0.1:8000."
          : err.message || "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  const visibleProducts = useMemo(() => {
    let list = [...products];

    if (showFavoritesOnly) {
      list = list.filter((p) =>
        favorites.includes(p.product_id || p.title)
      );
    }
    list = list.filter((p) => Number(p.rating || 0) >= Number(minRating));
    if (sort === "price-low") list.sort((a, b) => Number(a.price ?? Infinity) - Number(b.price ?? Infinity));
    if (sort === "price-high") list.sort((a, b) => Number(b.price ?? -Infinity) - Number(a.price ?? -Infinity));
    if (sort === "rating") list.sort((a, b) => Number(b.rating || 0) - Number(a.rating || 0));
    return list;
  }, [products, activeCategory, minRating, sort, showFavoritesOnly, favorites]);

  function toggleFavorite(id) {
    setFavorites((old) => old.includes(id) ? old.filter((x) => x !== id) : [...old, id]);
  }

  return (
    <div className="app-shell">
      <div className="top-glow" />
      <header className="navbar">
        <a className="brand" href="#" aria-label="AgentLens home">
          <span className="brand-mark"><Sparkles size={20} /></span>
          <span>agent<span className="brand-light">lens</span><span className="brand-dot">.</span></span>
        </a>
        <div className="nav-center"><span className="status-dot" /> AI PRODUCT DISCOVERY</div>
        <a className="nav-link" href="#results">Explore <ArrowRight size={14} /></a>
      </header>

      <main>
        <section className="hero">
          <div className="eyebrow"><span className="eyebrow-icon"><Zap size={13} /></span> YOUR PERSONAL AI SHOPPING ASSISTANT</div>
          <h1>Less searching.<br /><span className="gradient-text">More discovering.</span></h1>
          <p className="hero-copy">Tell us what you need. AgentLens finds products that fit your preferences, budget, and lifestyle.</p>

          <form className="search-panel" onSubmit={(e) => { e.preventDefault(); searchProducts(); }}>
            <div className="search-input-row">
              <Sparkles className="search-sparkle" size={21} />
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Describe the product you're looking for..."
                aria-label="Describe the product you're looking for"
              />
              {question && <button type="button" className="clear-button" onClick={() => setQuestion("")} aria-label="Clear search"><X size={16} /></button>}
              <button className="search-button" type="submit" disabled={loading || !question.trim()}>
                {loading ? <LoaderCircle size={17} className="spin" /> : <>Discover <ArrowRight size={16} /></>}
              </button>
            </div>
            <div className="search-bottom">
              <span><span className="live-dot" /> Natural language enabled</span>
              <span className="search-hint">Be specific for better results</span>
            </div>
          </form>

          <div className="suggestions">
            <span className="suggestion-label">TRY ASKING</span>
            {suggestions.map(({ icon: Icon, text }) => (
              <button key={text} className="suggestion-chip" onClick={() => { setQuestion(text); searchProducts(text); }}>
                <Icon size={14} /> {text}
              </button>
            ))}
          </div>

          <div className="trust-row">
            <div><ShieldCheck size={16} /><span>Data-driven discovery</span></div>
            <span className="trust-separator" />
            <div><Activity size={16} /><span>Smart product matching</span></div>
            <span className="trust-separator" />
            <div><Zap size={16} /><span>Built for better choices</span></div>
          </div>
        </section>

        <section className="results-section" id="results">
          <div className="section-heading">
            <div>
              <div className="section-kicker">{hasSearched ? "YOUR DISCOVERIES" : "THE DISCOVERY SPACE"}</div>
              <h2>{hasSearched ? "Search results" : "Find your next favorite."}</h2>
              <p>{hasSearched ? answer || "Products matched to your search." : "Your next great find starts with a question."}</p>
            </div>
            {products.length > 0 && (
              <button className={`filter-toggle ${showFilters ? "selected" : ""}`} onClick={() => setShowFilters(!showFilters)}>
                <SlidersHorizontal size={16} /> Filters <ChevronDown size={14} />
              </button>
            )}
          </div>

          {showFilters && products.length > 0 && (
            <div className="filter-panel">
              <label>Minimum rating
                <select value={minRating} onChange={(e) => setMinRating(e.target.value)}>
                  <option value="0">Any rating</option>
                  <option value="3">3+ stars</option>
                  <option value="4">4+ stars</option>
                  <option value="4.5">4.5+ stars</option>
                </select>
              </label>
            </div>
          )}

          {products.length > 0 && (
  <div className="results-toolbar">
    <div className="toolbar-count">
      <span className="toolbar-count-number">{visibleProducts.length}</span>
      <span>{showFavoritesOnly ? "saved products" : "matching products"}</span>
    </div>

    <div className="toolbar-actions">
      <button
        type="button"
        className={`saved-toggle ${showFavoritesOnly ? "active" : ""}`}
        onClick={() => setShowFavoritesOnly(value => !value)}
      >
        <Heart size={15} fill={showFavoritesOnly ? "currentColor" : "none"} />
        {showFavoritesOnly ? "All results" : `Saved (${favorites.length})`}
      </button>

      <label className="toolbar-sort">
        <span>Sort by</span>
        <select
          value={sort}
          onChange={event => setSort(event.target.value)}
          aria-label="Sort products"
        >
          <option value="relevance">Best match</option>
          <option value="price-low">Price: low to high</option>
          <option value="price-high">Price: high to low</option>
          <option value="rating">Highest rated</option>
        </select>
      </label>
    </div>
  </div>
)}

          {loading ? (
            <div className="state-panel">
              <div className="loader-orbit"><Sparkles size={25} /><span /></div>
              <h3>Finding your best matches</h3>
              <p>AgentLens is searching the product graph for you...</p>
              <div className="loading-bars"><i /><i /><i /><i /><i /></div>
            </div>
          ) : error ? (
            <div className="state-panel error-panel">
              <div className="state-icon"><Activity size={24} /></div>
              <h3>{error.includes("No matching") ? "Nothing matched this time" : "Let's reconnect"}</h3>
              <p>{error}</p>
              <button className="retry-button" onClick={() => searchProducts()}>Try again <ArrowRight size={15} /></button>
            </div>
          ) : visibleProducts.length > 0 ? (
            <div className="product-grid">
              {visibleProducts.map((product, index) => {
                const id = product.product_id || product.title || String(index);
                const favorite = favorites.includes(id);
                return (
                  <article className="product-card" key={id}>
                    <div className="product-visual">
                      <ProductArt product={product} index={index} />
                      <span className="match-badge"><Sparkles size={11} /> MATCH</span>
                      <button className={`favorite-button ${favorite ? "favorited" : ""}`} onClick={() => toggleFavorite(id)} aria-label={favorite ? "Remove from favorites" : "Add to favorites"}>
                        <Heart size={17} fill={favorite ? "currentColor" : "none"} />
                      </button>
                    </div>
                    <div className="product-info">
                      <div className="product-meta">
                        <span>{product.store || product.category || getCategory(product)}</span>
                        {product.rating != null && <span className="rating"><Star size={13} fill="currentColor" /> {Number(product.rating).toFixed(1)}</span>}
                      </div>
                      <h3>{product.title || "Untitled product"}</h3>
                      <p className="product-description">{product.description || "A product selected from the AgentLens discovery catalog."}</p>
                      <div className="product-bottom">
                        <div className="price">
                          {product.price != null ? `$${Number(product.price).toFixed(2)}` : "Price unavailable"}
                          {product.rating_count > 0 && <span>{Number(product.rating_count).toLocaleString()} reviews</span>}
                        </div>
                        <button className="details-button" title="View product details" aria-label={`View details for ${product.title || "product"}`} onClick={() => setSelectedProduct(product)}>
                          <ArrowRight size={17} />
                        </button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-illustration">
                <div className="empty-orbit orbit-one" />
                <div className="empty-orbit orbit-two" />
                <div className="empty-core"><Search size={29} /></div>
                <span className="float-spark spark-one"><Sparkles size={17} /></span>
                <span className="float-spark spark-two"><Zap size={16} /></span>
              </div>
              <h3>Your next great find is out there.</h3>
              <p>Start with a product, a budget, or a wish list. We'll take it from there.</p>
              <div className="empty-hint"><Check size={14} /> Try a suggestion above to see real products</div>
            </div>
          )}
        </section>
      </main>

      {selectedProduct && (
        <div
          className="details-overlay"
          onClick={() => setSelectedProduct(null)}
          role="presentation"
        >
          <section
            className="details-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="details-title"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              className="details-close"
              onClick={() => setSelectedProduct(null)}
              aria-label="Close product details"
            >
              <X size={20} />
            </button>

            <div className="details-kicker">AGENTLENS PRODUCT DETAILS</div>
            <h2 id="details-title">{selectedProduct.title || "Untitled product"}</h2>

            <div className="details-price">
              {selectedProduct.price != null
                ? `$${Number(selectedProduct.price).toFixed(2)}`
                : "Price unavailable"}
            </div>

            <div className="details-stats">
              <span>Brand / Store: {selectedProduct.store || "Not specified"}</span>
              <span>Category: {getCategory(selectedProduct)}</span>
              <span>
                Rating: {selectedProduct.rating != null
                  ? `${Number(selectedProduct.rating).toFixed(1)} / 5`
                  : "Not available"}
              </span>
              <span>
                Reviews: {Number(selectedProduct.rating_count || 0).toLocaleString()}
              </span>
              <span>Product ID: {selectedProduct.product_id || "Not available"}</span>
            </div>

            <p className="details-description">
              {selectedProduct.description || "No additional description is available for this product in the current catalog."}
            </p>

            <button
              type="button"
              className="search-button details-done"
              onClick={() => setSelectedProduct(null)}
            >
              Done <Check size={16} />
            </button>
          </section>
        </div>
      )}

      <footer className="footer">
        <a className="brand footer-brand" href="#"><span className="brand-mark"><Sparkles size={16} /></span><span>agent<span className="brand-light">lens</span><span className="brand-dot">.</span></span></a>
        <span>Smarter discovery starts here.</span>
        <span className="footer-status"><span className="status-dot" /> POWERED BY AI + KNOWLEDGE GRAPHS</span>
      </footer>
    </div>
  );
}

export default App;
