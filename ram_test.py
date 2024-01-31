import modules.search_engine.search_engine as search_engine
qustion = "小幫手我想知道光合作用?"
ans = {}
ans["tf"] = search_engine.tf(user_input=qustion)
ans["mix"] = search_engine.sbert_mix_tf(user_input=qustion, except_article_ids=[
                                        x["article_id"] for x in ans["tf"]["alist"]])
ans["sbert"] = search_engine.sbert(user_input=qustion, except_article_ids=(
    [x["article_id"] for x in ans["tf"]["alist"]] + [x["_id"] for x in ans["mix"]["alist"]]))

print(ans["tf"]["comment_msg"])
print(ans["mix"]["comment_msg"])
print(ans["sbert"]["comment_msg"])