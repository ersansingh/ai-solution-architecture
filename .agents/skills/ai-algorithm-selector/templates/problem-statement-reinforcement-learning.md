# Reinforcement Learning Problem Statement Template

> **Paradigm**: Reinforcement Learning (Model-Based / Model-Free RL / Contextual Bandits / Offline RL)  
> **Skill Reference**: `.agents/skills/ai-algorithm-selector/SKILL.md`

---

## 1. Business Objective & Problem Definition
* **Business Objective**: [Optimize sequential decision-making policy over time under uncertainty]
* **Target Domain**: [e.g., Autonomous Trading / Dynamic Pricing / Robotics / Personalization Bandits / Energy Grid Control]
* **Current Baseline**: [e.g., Static heuristic policy / Rule-based state machine / A/B testing framework]

---

## 2. Markov Decision Process (MDP) Formulation
* **State Space ($\mathcal{S}$)**: [Vector of environment observations, historical states, agent status]
* **Action Space ($\mathcal{A}$)**: 
  * [ ] Discrete Action Space (e.g. {Buy, Sell, Hold} or {Select Ad 1..N})
  * [ ] Continuous Action Space (e.g. Steering angle $[-1.0, 1.0]$, Price adjustment $[-\$50, +\$50]$)
* **Reward Function ($\mathcal{R}(s, a, s')$)**: [Exact mathematical definition of immediate reward and penalties]
* **Discount Factor ($\gamma$)**: [e.g., $\gamma = 0.99$ for long-horizon optimization]
* **Horizon Type**: [Episodic (max steps $T$) vs Continuous Infinite Horizon]

---

## 3. Environment & Simulator Availability
* **Simulator Availability**: [Custom Gym/Gymnasium Environment / Physics Engine (MuJoCo/Isaac) / Historical Logged Data]
* **Environment Fidelity**: [Real-time interactive vs Offline batch log execution]
* **Exploration Safety**: [Are exploratory random actions allowed in production, or is Offline RL / Constrained RL required?]

---

## 4. Performance & Evaluation Criteria
* **Target Metric**: [Cumulative Episode Return $\sum \gamma^t R_t$ / Expected Reward Lift over Baseline]
* **Sample Efficiency**: [Maximum allowed environment interactions/steps during training]
* **Safety Boundaries**: [Hard constraint violations allowed: 0 (Requires Safe RL / Shielding)]
* **Inference Latency SLA**: [Control loop frequency e.g. < 5 ms for robotics or < 50 ms for web recommendation]

---

## 5. Deployment & Policy Execution
* **Learning Paradigm**: [On-Policy (PPO) / Off-Policy (SAC/DDPG) / Offline RL (CQL/IQL) / Contextual Bandit (LinUCB)]
* **Deployment Hardware**: [Edge microcontroller / GPU Server / Real-time API]
