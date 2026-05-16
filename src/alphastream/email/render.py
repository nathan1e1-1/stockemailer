from __future__ import annotations

from html import escape

from alphastream.types import EmailReport, RankedPick


def _format_market_cap(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    return f"${value:,.0f}"


def _format_price(value: float) -> str:
    return f"${value:,.2f}"


def _format_reported_value(value: float) -> str:
    if value <= 0:
        return "N/A"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    return f"${value:,.0f}"


def _render_pick_card(pick: RankedPick) -> str:
    badge_background = "#e2fbe8" if pick.section == "top_pick" else "#fff7db"
    badge_foreground = "#166534" if pick.section == "top_pick" else "#92400e"
    return f"""
        <section style="padding:20px 0;border-bottom:1px solid #e5e7eb;">
          <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;">
            <div>
              <h3 style="margin:0 0 8px;font-size:20px;line-height:1.2;">{escape(pick.ticker)} - {escape(pick.company_name)}</h3>
              <p style="margin:0 0 8px;color:#334155;"><strong>Strategy:</strong> {escape(pick.strategy_label)}</p>
              <p style="margin:0 0 8px;color:#334155;"><strong>Sector:</strong> {escape(pick.sector or "Unknown")}</p>
            </div>
            <div style="background:{badge_background};color:{badge_foreground};border-radius:999px;padding:8px 12px;font-weight:600;white-space:nowrap;">
              {pick.score.total_score}/100
            </div>
          </div>
          <p style="margin:6px 0;"><strong>Signal:</strong> {escape(pick.score.signal_label)}</p>
          <p style="margin:6px 0;"><strong>The Whale:</strong> {escape(pick.investor_name)}. {escape(pick.whale_note)}</p>
          <p style="margin:6px 0;"><strong>Sentiment:</strong> {escape(pick.sentiment_note)}</p>
          <p style="margin:6px 0;"><strong>Lead Headline:</strong> {escape(pick.headline_summary or "No additional summary available.")}</p>
          <p style="margin:6px 0;"><strong>Trend:</strong> {escape(pick.trend_note)}</p>
          <table role="presentation" style="width:100%;margin-top:12px;border-collapse:collapse;font-size:14px;">
            <tr>
              <td style="padding:8px;border:1px solid #e5e7eb;"><strong>Reported Value</strong><br>{_format_reported_value(pick.reported_value)}</td>
              <td style="padding:8px;border:1px solid #e5e7eb;"><strong>Market Cap</strong><br>{_format_market_cap(pick.market_cap)}</td>
              <td style="padding:8px;border:1px solid #e5e7eb;"><strong>Price</strong><br>{_format_price(pick.current_price)}</td>
              <td style="padding:8px;border:1px solid #e5e7eb;"><strong>200D MA</strong><br>{_format_price(pick.moving_average_200)}</td>
              <td style="padding:8px;border:1px solid #e5e7eb;"><strong>RSI</strong><br>{pick.rsi_14:.1f}</td>
            </tr>
          </table>
          <p style="margin:12px 0 0;"><strong>Score Breakdown:</strong> Institutional Conviction {pick.score.institutional_score}, News Sentiment {pick.score.sentiment_score}, Technical Trend {pick.score.technical_score}</p>
        </section>
        """


def _render_section(title: str, description: str, picks: list[RankedPick]) -> str:
    if not picks:
        return ""
    cards = "".join(_render_pick_card(pick) for pick in picks)
    return f"""
      <section style="margin-top:24px;">
        <h2 style="margin:0 0 8px;font-size:22px;">{escape(title)}</h2>
        <p style="margin:0 0 4px;color:#475569;">{escape(description)}</p>
        {cards}
      </section>
    """


def _render_report_summary(report: EmailReport, top_picks: list[RankedPick], watchlist: list[RankedPick]) -> str:
    return f"""
      <section style="margin:0 0 20px;padding:16px;border-radius:14px;background:#eff6ff;">
        <h2 style="margin:0 0 12px;font-size:20px;">Daily Summary</h2>
        <table role="presentation" style="width:100%;border-collapse:collapse;font-size:14px;">
          <tr>
            <td style="padding:8px;border:1px solid #bfdbfe;"><strong>Total Names</strong><br>{len(report.picks)}</td>
            <td style="padding:8px;border:1px solid #bfdbfe;"><strong>Top Picks</strong><br>{len(top_picks)}</td>
            <td style="padding:8px;border:1px solid #bfdbfe;"><strong>Watchlist</strong><br>{len(watchlist)}</td>
          </tr>
          <tr>
            <td style="padding:8px;border:1px solid #bfdbfe;"><strong>Investors Scanned</strong><br>{report.investors_scanned}</td>
            <td style="padding:8px;border:1px solid #bfdbfe;"><strong>Positions Scanned</strong><br>{report.positions_scanned}</td>
            <td style="padding:8px;border:1px solid #bfdbfe;"><strong>Warnings</strong><br>{len(report.warnings)}</td>
          </tr>
        </table>
      </section>
    """


def _render_warnings(warnings: list[str]) -> str:
    if not warnings:
        return ""
    items = "".join(f"<li style=\"margin:0 0 6px;\">{escape(warning)}</li>" for warning in warnings)
    return f"""
      <section style="margin-top:24px;">
        <h2 style="margin:0 0 8px;font-size:22px;">Warnings and Data Quality Notes</h2>
        <p style="margin:0 0 8px;color:#475569;">Some symbols or data providers returned incomplete results during this run.</p>
        <ul style="margin:0;padding-left:20px;color:#334155;">
          {items}
        </ul>
      </section>
    """


def render_email(report: EmailReport) -> str:
    top_picks = [pick for pick in report.picks if pick.section == "top_pick"]
    watchlist = [pick for pick in report.picks if pick.section == "watchlist"]
    if not report.picks:
        sections = "<p style=\"margin:0;\">No high-conviction picks passed the filters this run.</p>"
    else:
        sections = (
            _render_section(
                "Top Picks",
                "Highest-conviction names from the current filing, sentiment, and technical ranking model.",
                top_picks,
            )
            + _render_section(
                "Watchlist",
                "Lower-conviction names that still cleared the base filters and are worth monitoring.",
                watchlist,
            )
        )
    return f"""
    <!DOCTYPE html>
    <html lang="en">
      <body style="margin:0;padding:24px;background:#f8fafc;color:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
        <main style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:16px;padding:24px;">
          <h1 style="margin-top:0;">AlphaStream Daily Picks</h1>
          <p style="margin:0 0 8px;color:#475569;">Run date: {escape(report.generated_on)} ({escape(report.timezone_name)})</p>
          <p style="margin:0 0 20px;color:#475569;">High-conviction ideas ranked from institutional conviction, recent news sentiment, and technical trend checks.</p>
          {_render_report_summary(report, top_picks, watchlist)}
          {sections}
          {_render_warnings(report.warnings)}
          <p style="margin-top:24px;font-size:13px;color:#475569;">
            Top Picks are the strongest-ranked names. Watchlist names cleared the base filters but scored lower than the top section. Informational only. AlphaStream is a read-only research assistant and does not place trades or provide fiduciary advice.
          </p>
        </main>
      </body>
    </html>
    """.strip()
