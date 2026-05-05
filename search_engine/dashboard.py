"""HTML dashboard for search engine monitoring."""


def generate_dashboard(
    index_stats: dict,
    query_performance: dict,
    query_types: dict,
    trending_queries: list,
    zero_result_queries: list
) -> str:
    """Generate HTML dashboard for search engine."""

    trending_html = ""
    for query, count in trending_queries[:10]:
        trending_html += f"<tr><td>{query}</td><td>{count}</td></tr>"

    zero_result_html = ""
    for query in zero_result_queries[:5]:
        zero_result_html += f"<tr><td>{query}</td></tr>"

    query_types_html = ""
    for qtype, stats in query_types.items():
        query_types_html += f"""
        <tr>
            <td>{qtype.title()}</td>
            <td>{stats['count']}</td>
            <td>{stats['avg_time_ms']:.2f}</td>
            <td>{stats['percent']:.1f}%</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Search Engine Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #06b6d4, #0891b2); padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .header h1 {{ margin: 0; color: white; }}
            .metrics {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-bottom: 20px; }}
            .metric {{ background: linear-gradient(135deg, #1e3a8a, #1e40af); padding: 15px; border-radius: 8px; border-left: 4px solid #06b6d4; }}
            .metric .label {{ font-size: 12px; color: #94a3b8; margin-bottom: 5px; }}
            .metric .value {{ font-size: 24px; font-weight: bold; color: #06b6d4; }}
            .section {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
            .section h2 {{ margin: 0 0 15px 0; color: #06b6d4; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ background: #0f172a; padding: 10px; text-align: left; font-size: 12px; color: #94a3b8; border-bottom: 2px solid #334155; }}
            td {{ padding: 10px; border-bottom: 1px solid #334155; }}
            tr:hover {{ background: #0f172a; }}
            .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 40px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 Search Engine Dashboard</h1>
        </div>

        <div class="metrics">
            <div class="metric">
                <div class="label">Total Documents</div>
                <div class="value">{index_stats.get('total_documents', 0):,}</div>
            </div>
            <div class="metric">
                <div class="label">Total Searches</div>
                <div class="value">{query_performance.get('total_searches', 0):,}</div>
            </div>
            <div class="metric">
                <div class="label">Avg Exec Time</div>
                <div class="value">{query_performance.get('avg_exec_time_ms', 0):.2f}ms</div>
            </div>
            <div class="metric">
                <div class="label">Avg Results</div>
                <div class="value">{query_performance.get('avg_result_count', 0):.1f}</div>
            </div>
            <div class="metric">
                <div class="label">Index Terms</div>
                <div class="value">{index_stats.get('total_terms', 0):,}</div>
            </div>
        </div>

        <div class="section">
            <h2>Query Performance</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Total Searches</td>
                    <td>{query_performance.get('total_searches', 0):,}</td>
                </tr>
                <tr>
                    <td>Zero Result Searches</td>
                    <td>{query_performance.get('zero_result_searches', 0)}</td>
                </tr>
                <tr>
                    <td>Zero Result %</td>
                    <td>{query_performance.get('zero_result_percent', 0):.1f}%</td>
                </tr>
                <tr>
                    <td>Avg Execution Time</td>
                    <td>{query_performance.get('avg_exec_time_ms', 0):.2f}ms</td>
                </tr>
                <tr>
                    <td>Min Execution Time</td>
                    <td>{query_performance.get('min_exec_time_ms', 0):.2f}ms</td>
                </tr>
                <tr>
                    <td>Max Execution Time</td>
                    <td>{query_performance.get('max_exec_time_ms', 0):.2f}ms</td>
                </tr>
                <tr>
                    <td>P95 Execution Time</td>
                    <td>{query_performance.get('p95_exec_time_ms', 0):.2f}ms</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h2>Query Types</h2>
            <table>
                <tr>
                    <th>Type</th>
                    <th>Count</th>
                    <th>Avg Time (ms)</th>
                    <th>Percent</th>
                </tr>
                {query_types_html}
            </table>
        </div>

        <div class="section">
            <h2>Trending Queries</h2>
            <table>
                <tr>
                    <th>Query</th>
                    <th>Count</th>
                </tr>
                {trending_html}
            </table>
        </div>

        <div class="section">
            <h2>Zero Result Queries</h2>
            <table>
                <tr>
                    <th>Query</th>
                </tr>
                {zero_result_html}
            </table>
        </div>

        <div class="section">
            <h2>Index Statistics</h2>
            <table>
                <tr>
                    <th>Statistic</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Total Documents</td>
                    <td>{index_stats.get('total_documents', 0):,}</td>
                </tr>
                <tr>
                    <td>Total Terms</td>
                    <td>{index_stats.get('total_terms', 0):,}</td>
                </tr>
                <tr>
                    <td>Total Postings</td>
                    <td>{index_stats.get('total_postings', 0):,}</td>
                </tr>
                <tr>
                    <td>Avg Postings Per Term</td>
                    <td>{index_stats.get('average_postings_per_term', 0):.2f}</td>
                </tr>
                <tr>
                    <td>Index Size (MB)</td>
                    <td>{index_stats.get('index_size_mb', 0):.2f}</td>
                </tr>
                <tr>
                    <td>Capacity Usage</td>
                    <td>{index_stats.get('capacity_percent', 0):.1f}%</td>
                </tr>
            </table>
        </div>

        <div class="footer">
            <p>Search Engine Dashboard | Real-Time Monitoring</p>
        </div>

    </body>
    </html>
    """

    return html
