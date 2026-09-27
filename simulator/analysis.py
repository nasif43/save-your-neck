import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

def generate_report(results_file, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(results_file, 'r') as f:
        data = json.load(f)
        
    df = pd.DataFrame(data)
    
    # 1. Game Length Dist
    plt.figure(figsize=(10,6))
    sns.boxplot(x='num_players', y='game_length_turns', data=df)
    plt.title('Game Length by Player Count')
    plt.savefig(f'{out_dir}/game_length.png')
    plt.close()
    
    # 2. Win Rate Dist
    if 'winner_strategy' in df.columns:
        win_rates = df['winner_strategy'].value_counts(normalize=True).reset_index()
        win_rates.columns = ['Strategy', 'Win Rate']
        plt.figure(figsize=(10,6))
        sns.barplot(x='Win Rate', y='Strategy', data=win_rates)
        plt.title('Win Rate by Strategy')
        plt.savefig(f'{out_dir}/win_rates.png')
        plt.close()

    # 4. Death Timings
    if 'death_turns' in df.columns:
        all_deaths = []
        for d in df['death_turns']:
            all_deaths.extend(d)
        plt.figure(figsize=(10,6))
        sns.histplot(all_deaths, bins=30, kde=True)
        plt.title('Distribution of Death Timings (Turns)')
        plt.xlabel('Turn Number')
        plt.savefig(f'{out_dir}/death_timings.png')
        plt.close()
        
    # 5. Ghost stats
    stats = ['ghost_encounters', 'ghosts_survived', 'ghosts_removed']
    means = df[stats].mean().reset_index()
    means.columns = ['Metric', 'Average per Game']
    plt.figure(figsize=(8,5))
    sns.barplot(x='Average per Game', y='Metric', data=means)
    plt.title('Ghost Interaction Rates')
    plt.savefig(f'{out_dir}/ghost_stats.png')
    plt.close()

    # 6. Trade stats
    trade_stats = ['trades_attempted', 'trades_successful']
    means_t = df[trade_stats].mean().reset_index()
    means_t.columns = ['Metric', 'Average per Game']
    plt.figure(figsize=(8,4))
    sns.barplot(x='Average per Game', y='Metric', data=means_t)
    plt.title('Trade Statistics')
    plt.savefig(f'{out_dir}/trade_stats.png')
    plt.close()

    
    # 7. Threat Curve
    if "ghost_events" in df.columns:
        all_events = []
        for index, row in df.iterrows():
            if isinstance(row["ghost_events"], list):
                all_events.extend(row["ghost_events"])
        
        if all_events:
            events_df = pd.DataFrame(all_events)
            if not events_df.empty and "turn" in events_df.columns:
                plt.figure(figsize=(12, 6))
                
                # We can group by turn and event type
                event_counts = events_df.groupby(["turn", "event"]).size().unstack(fill_value=0)
                
                # Smoothing
                event_counts = event_counts.rolling(window=5, min_periods=1).mean()
                
                if not event_counts.empty:
                    event_counts.plot(kind="line", ax=plt.gca(), linewidth=2)
                    plt.title("Ghost Threat Curve (Moving Average over Turns)")
                    plt.xlabel("Turn Number")
                    plt.ylabel("Avg Events per Turn")
                    plt.savefig(f"{out_dir}/threat_curve.png")
                plt.close()

    # Generate Flowchart (Mermaid)
    mermaid_code = """
    graph TD
        A[Turn Start] --> B[Utility Phase]
        B -->|Play Utility| B
        B --> C[Draw Phase]
        C -->|Normal Card| D[Add to Hand]
        C -->|Ghost| E[Resolve Ghost]
        D --> F[End Turn]
        E --> G{Has Protection?}
        G -->|Yes 2x| H[Remove Ghost Permanently]
        G -->|Yes 1x| I[Survive, Bury Ghost]
        G -->|No| J[Trade Attempt]
        J -->|Success| I
        J -->|Fail| K[Death, Bury Ghost]
        H --> F
        I --> F
        K --> F
    """

    # Create HTML
    html = f"""
    <html>
    <head>
        <title>Save Your Neck - Simulation Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f4f4f4; }}
            .container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 900px; margin: auto; }}
            h1, h2 {{ color: #333; }}
            img {{ max-width: 100%; border: 1px solid #ddd; margin-top: 10px; }}
            pre {{ background: #eee; padding: 10px; }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{startOnLoad:true}});</script>
    </head>
    <body>
        <div class="container">
            <h1>Save Your Neck Simulation Report</h1>
            <p>Generated based on {len(df)} simulated games.</p>
            
            
            <h2>Strategy Behaviors Defined</h2>
            <ul>
                <li><b>Aggressive:</b> Focuses on eliminating opponents by aggressively playing Attack, Chor, Shakchunni, and Robber to strip away hands and force deadly draws.</li>
                <li><b>Coward:</b> Plays defensively. Aggressively preserves protection cards and rarely initiates attacks, preferring to Skip or Draw to survive as long as possible.</li>
                <li><b>Opportunist:</b> Targets the weakest or strongest players dynamically (e.g., uses Chor on players with many cards, or Attacks vulnerable players with small hands).</li>
                <li><b>ProtectionHoarder:</b> Focuses solely on acquiring and hoarding Protection cards. Avoids playing utilities and rarely trades unless forced.</li>
                <li><b>Conservative:</b> Maximizes long-term resource value. Avoids playing utilities unless expected value is heavily positive.</li>
                <li><b>Chaos:</b> Maximizes disruption. Frequently triggers Shuffles, Reverses, and Robbers just to randomize the table state and induce unpredictable outcomes.</li>
                <li><b>Adaptive:</b> Uses a weighted heuristic that evaluates survival probability, hand sizes, and deck size to mathematically choose the optimal action.</li>
                <li><b>Random:</b> Plays legal actions completely at random. Used as a baseline to detect balance issues.</li>
            </ul>

            <h2>1. State Transition Diagram</h2>
            <div class="mermaid">
            {mermaid_code}
            </div>
            
            <h2>2. Game Length Distribution</h2>
            <img src="plots/game_length.png" />
            
            <h2>3. Strategy Win Rates</h2>
            <img src="plots/win_rates.png" />
            
            <h2>4. Death Timing Distribution</h2>
            <img src="plots/death_timings.png" />
            
            <h2>5. Ghost Interaction Statistics</h2>
            <img src="plots/ghost_stats.png" />
            
            <h2>6. Trade Statistics</h2>
            <img src="plots/trade_stats.png" />
            <h2>7. Threat Curve</h2>
            <img src="plots/threat_curve.png" />
            
        </div>
    </body>
    </html>
    """
    
    with open(f'{out_dir}/../REPORT.html', 'w') as f:
        f.write(html)
