from app.orchestration.haiku_agents import HaikuAgents

agents = HaikuAgents()
res =  agents.run_sync("recursion in programming")
print(f'Subject: {res.subject}')
print(f'Haiku: {res.haiku}')
print(f'Score: {res.score}')




