import modules.search_engine.search_engine as search_engine
qustion = "光合作用?"
ans = {}
#ans["tf"] = search_engine.tf(user_input=qustion)
#ans["mix"] = search_engine.sbert_mix_tf(user_input=qustion)
ans["sbert"] = search_engine.sbert(user_input=qustion)

print(ans["sbert"]["comment_msg"])