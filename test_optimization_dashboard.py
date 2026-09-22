#!/usr/bin/env python3
"""
Smart Room Dashboard - GA/PSO Integration Test Script
Quickly test sending optimization data to dashboard
"""

import requests
import json
import time
import random

# Configuration
DASHBOARD_URL = "http://172.20.0.65:5000"

def send_optimization_data(ga_fitness, pso_fitness, runs=1):
    """Send optimization results to Flask dashboard via HTTP API"""
    try:
        url = f"{DASHBOARD_URL}/api/optimization/update"
        data = {
            'ga_fitness': ga_fitness,
            'pso_fitness': pso_fitness,
            'runs': runs
        }
        
        print(f"\n📤 Sending to dashboard...")
        print(f"   GA Fitness:  {ga_fitness:.2f}")
        print(f"   PSO Fitness: {pso_fitness:.2f}")
        print(f"   Runs: {runs}")
        
        response = requests.post(url, json=data, timeout=3)
        
        if response.status_code == 200:
            print(f"✅ Dashboard updated successfully!")
            return True
        else:
            print(f"❌ Dashboard update failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to dashboard at {DASHBOARD_URL}")
        print(f"   Make sure Flask app is running!")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def simulate_optimization_cycle():
    """Simulate GA/PSO optimization cycle with random realistic fitness values"""
    print("\n" + "="*60)
    print("🤖 SIMULATING OPTIMIZATION CYCLE")
    print("="*60)
    
    # Simulate realistic fitness values (0-100 range)
    ga_fitness = random.uniform(75, 95)
    pso_fitness = random.uniform(75, 95)
    
    winner = "GA" if ga_fitness > pso_fitness else "PSO"
    winner_fitness = max(ga_fitness, pso_fitness)
    
    print(f"\n🧬 Genetic Algorithm Result:")
    print(f"   Fitness: {ga_fitness:.2f}/100")
    
    print(f"\n🐦 PSO Result:")
    print(f"   Fitness: {pso_fitness:.2f}/100")
    
    print(f"\n🏆 Winner: {winner} (Fitness: {winner_fitness:.2f})")
    
    # Send to dashboard
    success = send_optimization_data(ga_fitness, pso_fitness, runs=1)
    
    if success:
        print(f"\n✨ Open dashboard to see results:")
        print(f"   {DASHBOARD_URL}")
        print(f"\n   Check 'GA Optimization' and 'PSO Optimization' cards")
    
    return success

def continuous_simulation(interval=30):
    """Run continuous optimization simulation"""
    print("\n" + "="*60)
    print("🔄 CONTINUOUS OPTIMIZATION SIMULATION")
    print("="*60)
    print(f"Sending optimization data every {interval} seconds")
    print(f"Press Ctrl+C to stop\n")
    
    run_count = 0
    
    try:
        while True:
            run_count += 1
            
            print(f"\n--- Run #{run_count} ---")
            
            ga_fitness = random.uniform(75, 95)
            pso_fitness = random.uniform(75, 95)
            
            success = send_optimization_data(ga_fitness, pso_fitness, run_count)
            
            if success:
                print(f"⏳ Waiting {interval} seconds until next cycle...")
                time.sleep(interval)
            else:
                print("❌ Failed to send data. Retrying in 5 seconds...")
                time.sleep(5)
                
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Simulation stopped after {run_count} runs")
        print(f"✅ Total successful updates: {run_count}")

def main():
    """Main function with menu"""
    print("\n" + "="*60)
    print("  📊 Smart Room Dashboard - GA/PSO Test Tool")
    print("="*60)
    
    # Check dashboard connectivity
    print("\n🔍 Checking dashboard connection...")
    try:
        response = requests.get(DASHBOARD_URL, timeout=3)
        if response.status_code == 200:
            print(f"✅ Dashboard is reachable at {DASHBOARD_URL}")
        else:
            print(f"⚠️  Dashboard returned HTTP {response.status_code}")
    except:
        print(f"❌ Cannot reach dashboard at {DASHBOARD_URL}")
        print(f"   Make sure Flask app is running!")
        print(f"\n   Start it with:")
        print(f"   cd ~/smartroom/dashboard && source ~/smartroom/venv/bin/activate && python app.py")
        return
    
    # Menu
    while True:
        print("\n" + "="*60)
        print("Select an option:")
        print("="*60)
        print("1. Send single test data")
        print("2. Simulate optimization cycle (random values)")
        print("3. Continuous simulation (every 30s)")
        print("4. Custom values")
        print("5. Exit")
        print("="*60)
        
        try:
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == '1':
                # Test with fixed values
                send_optimization_data(85.5, 92.3, 1)
                
            elif choice == '2':
                # Single random simulation
                simulate_optimization_cycle()
                
            elif choice == '3':
                # Continuous simulation
                continuous_simulation(30)
                
            elif choice == '4':
                # Custom values
                try:
                    ga = float(input("Enter GA fitness (0-100): "))
                    pso = float(input("Enter PSO fitness (0-100): "))
                    runs = int(input("Enter run count: "))
                    send_optimization_data(ga, pso, runs)
                except ValueError:
                    print("❌ Invalid input. Please enter numbers.")
                    
            elif choice == '5':
                print("\n👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break

if __name__ == '__main__':
    main()
