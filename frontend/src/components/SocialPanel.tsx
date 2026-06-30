import type { SocialIntelligenceReport } from '../api';

interface Props {
  report: SocialIntelligenceReport | null;
  loading: boolean;
}

function sentimentClass(score: number): string {
  if (score >= 75) return 'high';
  if (score >= 55) return 'medium';
  return 'low';
}

export default function SocialPanel({ report, loading }: Props) {
  if (loading) {
    return <div className="loading">Loading social intelligence...</div>;
  }

  if (!report) {
    return (
      <div className="empty-state" style={{ padding: '2rem 1rem' }}>
        <p>Select a city to see Google reviews, Instagram buzz, and X/Twitter shopping signals.</p>
      </div>
    );
  }

  const liveSources = Object.entries(report.data_sources)
    .filter(([, v]) => v)
    .map(([k]) => k.replace('_live', ''))
    .join(', ');

  return (
    <div className="social-panel">
      <section className="sidebar-section">
        <h2>
          Social Intelligence
          {report.ai_verified && (
            <span className="ai-badge" title="Review sentiment verified by OpenAI">AI Verified</span>
          )}
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          {report.location}, {report.city}
        </p>

        <div className="social-overview">
          <div className="social-stat">
            <span className="social-stat-value">{report.overall_sentiment_score}</span>
            <span className="social-stat-label">Sentiment</span>
            <span className={`sentiment-badge ${sentimentClass(report.overall_sentiment_score)}`}>
              {report.overall_sentiment_label}
            </span>
          </div>
          <div className="social-stat">
            <span className="social-stat-value">{report.shopping_intent_score}</span>
            <span className="social-stat-label">Shopping Intent</span>
          </div>
        </div>

        <p className="recommendation" style={{ marginTop: '1rem' }}>{report.summary}</p>

        {liveSources && (
          <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            Live data: {liveSources}
          </p>
        )}

        {report.review_insights && report.review_insights.length > 0 && (
          <div style={{ marginTop: '1rem' }}>
            <h3 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>
              AI Review Insights
            </h3>
            <ul style={{ fontSize: '0.85rem', paddingLeft: '1.2rem', color: 'var(--text-secondary)' }}>
              {report.review_insights.map((insight, i) => (
                <li key={i} style={{ marginBottom: '0.35rem' }}>{insight}</li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section className="sidebar-section">
        <h2>Where People Shop</h2>
        <ul className="shopping-dest-list">
          {report.shopping_destinations.map((d, i) => (
            <li key={d.name}>
              <div className="dest-rank">#{i + 1}</div>
              <div className="dest-info">
                <strong>{d.name}</strong>
                <span>{d.why_popular}</span>
                <div className="dest-metrics">
                  <span>Buzz {d.social_buzz_score}</span>
                  <span>★ {d.google_rating}</span>
                  <span>{d.instagram_mentions} IG mentions</span>
                  <span className="dest-tag">{d.best_for}</span>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="sidebar-section">
        <h2><span className="platform-badge google">G</span> Google Reviews</h2>
        <div className="platform-stats">
          <span>★ {report.google.average_rating ?? 4.4} avg</span>
          <span>{report.google.total_reviews?.toLocaleString() ?? 0} reviews</span>
          <span>Sentiment {report.google.sentiment_score}%</span>
        </div>
        <ul className="review-list">
          {(report.google.reviews ?? []).slice(0, 5).map((r, i) => (
            <li key={i}>
              <div className="review-header">
                <strong>{r.author}</strong>
                {r.rating != null && <span className="review-stars">{'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}</span>}
                <span className="review-time">{r.time}</span>
              </div>
              <p>{r.text}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="sidebar-section">
        <h2><span className="platform-badge instagram">IG</span> Instagram</h2>
        <div className="platform-stats">
          <span>{report.instagram.mention_volume_monthly?.toLocaleString() ?? 0} mentions/mo</span>
          <span>{report.instagram.engagement_rate ?? 0}% engagement</span>
          <span>{report.instagram.influencer_visits_monthly ?? 0} influencer visits</span>
        </div>
        <div className="hashtag-cloud">
          {(report.instagram.shopping_tags ?? []).map((tag) => (
            <span key={tag} className="hashtag">{tag}</span>
          ))}
        </div>
        <ul className="social-post-list">
          {(report.instagram.top_posts ?? []).slice(0, 4).map((p, i) => (
            <li key={i}>
              <p>{p.caption as string}</p>
              <span>❤️ {(p.likes as number)?.toLocaleString()} · 💬 {p.comments as number}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="sidebar-section">
        <h2><span className="platform-badge twitter">X</span> Twitter / X</h2>
        <div className="platform-stats">
          <span>{report.twitter.mention_volume_monthly ?? 0} mentions/mo</span>
          <span>{report.twitter.shopping_intent_mentions ?? 0} shopping intent</span>
          <span>Sentiment {report.twitter.sentiment_score}%</span>
        </div>
        <div className="trending-topics">
          {(report.twitter.trending_topics ?? []).map((t) => (
            <span key={t} className="trending-topic">{t}</span>
          ))}
        </div>
        <ul className="social-post-list">
          {(report.twitter.top_posts ?? []).slice(0, 4).map((p, i) => (
            <li key={i}>
              <p>{p.text as string}</p>
              <span>❤️ {p.likes as number} · 🔁 {p.retweets as number}</span>
            </li>
          ))}
        </ul>
      </section>

      {(report.top_positive_themes.length > 0 || report.top_negative_themes.length > 0) && (
        <section className="sidebar-section">
          <h2>Sentiment Themes</h2>
          {report.top_positive_themes.length > 0 && (
            <div className="theme-group positive">
              <span className="theme-label">Positive</span>
              {report.top_positive_themes.map((t) => (
                <span key={t} className="theme-chip">{t}</span>
              ))}
            </div>
          )}
          {report.top_negative_themes.length > 0 && (
            <div className="theme-group negative">
              <span className="theme-label">Concerns</span>
              {report.top_negative_themes.map((t) => (
                <span key={t} className="theme-chip">{t}</span>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
