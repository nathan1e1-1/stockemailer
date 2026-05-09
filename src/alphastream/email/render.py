from __future__ import annotations

from html import escape

from alphastream.types import RankedPick


def render_email(picks: list[RankedPick]) -> str:
    items = []
    for pick in picks:
        items.append(
            f"""
            <section style="padding:16px 0;border-bottom:1px solid #e5e7eb;">
              <h2 style="margin:0 0 8px;font-size:20px;">{escape(pick.ticker)} - {escape(pick.company_name)}</h2>
              <p style="margin:4px 0;"><strong>Score:</strong> {pick.score.total_score}/100 ({escape(pick.score.signal_label)})</p>
              <p style="margin:4px 0;"><strong>The Whale:</strong> {escape(pick.investor_name)}</p>
              <p style="margin:4px 0;"><strong>Sentiment:</strong> {escape(pick.summary)}</p>
              <p style="margin:4px 0;"><strong>Trend:</strong> {escape(pick.trend_note)}</p>
              <p style="margin:4px 0;"><strong>Strategy:</strong> {escape(pick.strategy_label)}</p>
            </section>
            """
        )
    sections = "".join(items) or "<p style=\"margin:0;\">No high-conviction picks passed the filters this run.</p>"
    return f"""
    <!DOCTYPE html>
    <html lang="en">
      <body style="margin:0;padding:24px;background:#f8fafc;color:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
        <main style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:16px;padding:24px;">
          <h1 style="margin-top:0;">AlphaStream Weekly Picks</h1>
          {sections}
          <p style="margin-top:24px;font-size:13px;color:#475569;">
            Informational only. AlphaStream is a read-only research assistant and does not place trades or provide fiduciary advice.
          </p>
        </main>
      </body>
    </html>
    """.strip()
