# Setup environment value
import os
from dotenv import load_dotenv
load_dotenv()


## anthropic
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
anthropic_api_key = os.getenv("anthropic_api_key")
anthropic = Anthropic(api_key=anthropic_api_key)

## openai
import openai
openai_api_key = os.getenv("openai_api_key")
openai.api_key = openai_api_key

## RoBERTa
# https://huggingface.co/uer/roberta-base-chinese-extractive-qa
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
RoBERTa_model = AutoModelForQuestionAnswering.from_pretrained('uer/roberta-base-chinese-extractive-qa')
RoBERTa_tokenizer = AutoTokenizer.from_pretrained('uer/roberta-base-chinese-extractive-qa')
RoBERTa_QA = pipeline('question-answering',model=RoBERTa_model, tokenizer=RoBERTa_tokenizer)

## bert
# https://huggingface.co/NchuNLP/Chinese-Question-Answering?context=%E6%A0%B9%E6%93%9A+%E9%A4%98%E8%A7%92%E9%97%9C%E4%BF%82+(Trigonometric+Identities+for+Complementary+Angles)%E5%9C%8B%E7%AB%8B%E8%98%AD%E9%99%BD%E5%A5%B3%E4%B8%AD%E6%95%B8%E5%AD%B8%E7%A7%91%E9%99%B3%E6%95%8F%E6%99%A7%E8%80%81%E5%B8%AB/%E5%9C%8B%E7%AB%8B%E8%87%BA%E7%81%A3%E5%B8%AB%E7%AF%84%E5%A4%A7%E5%AD%B8%E6%95%B8%E5%AD%B8%E7%B3%BB%E6%B4%AA%E8%90%AC%E7%94%9F%E6%95%99%E6%8E%88%E8%B2%AC%E4%BB%BB%E7%B7%A8%E8%BC%AF%E5%9C%A8+%5C%5CDelta%7BABC%7D+%E4%B8%AD%EF%BC%8C%E8%8B%A5+%5C%5Cangle%7BABC%7D%3D90%5E%5C%5Ccirc%EF%BC%8C%E5%89%87+%5C%5Cangle%7BA%7D+%5C%5Cangle%7BB%7D%3D90%5E%5C%5Ccirc%EF%BC%8C%E5%A6%82%E4%B8%8B%E5%9C%96%E4%B8%80%E6%89%80%E7%A4%BA%EF%BC%9A%E5%9C%96%E4%B8%80%EF%BC%9A%E7%8F%BE%E8%A1%8C%E9%AB%98%E4%B8%AD%E6%95%B8%E5%AD%B8%E6%95%99%E7%A7%91%E6%9B%B8%EF%BC%8C%E9%8A%B3%E8%A7%92%E4%B8%89%E8%A7%92%E5%87%BD%E6%95%B8%E7%9A%84%E5%AE%9A%E7%BE%A9%E6%98%AF%E5%BB%BA%E7%AB%8B%E5%9C%A8%E7%9B%B4%E8%A7%92%E4%B8%89%E8%A7%92%E5%BD%A2%E4%B8%8A%E3%80%82%E6%A0%B9%E6%93%9A%E4%B8%89%E8%A7%92%E5%87%BD%E6%95%B8%E7%9A%84%E5%9F%BA%E6%9C%AC%E5%AE%9A%E7%BE%A9%EF%BC%8C%E5%9B%A0%E7%82%BA+%5C%5Cangle%7BA%7D+%E7%9A%84%E5%B0%8D%E9%82%8A+%5C%5Coverline%7BBC%7D+%E6%81%B0%E7%82%BA+%5C%5Cangle%7BB%7D+%E7%9A%84%E9%84%B0%E9%82%8A%EF%BC%8C%E4%B8%94+%5C%5Cangle%7BB%7D+%E7%9A%84%E5%B0%8D%E9%82%8A+%5C%5Coverline%7BAC%7D+%E6%81%B0%E7%82%BA+%5C%5Cangle%7BA%7D+%E7%9A%84%E9%84%B0%E9%82%8A%E3%80%82%E5%89%87%5C%5Cdisplaystyle%5C%5Csin%7BA%7D%3D%5C%5Cfrac%7Ba%7D%7Bc%7D%3D%5C%5Ccos%7BB%7D%EF%BC%8C%5C%5Cdisplaystyle%5C%5Ccos%7BA%7D%3D%5C%5Cfrac%7Bb%7D%7Bc%7D%3D%5C%5Csin%7BB%7D%EF%BC%8C%5C%5Cdisplaystyle%5C%5Ctan%7BA%7D%3D%5C%5Cfrac%7Ba%7D%7Bb%7D%3D%5C%5Ccot%7BB%7D%EF%BC%8C%5C%5Cdisplaystyle%5C%5Ccot%7BA%7D%3D%5C%5Cfrac%7Bb%7D%7Ba%7D%3D%5C%5Ctan%7BB%7D%EF%BC%8C%5C%5Cdisplaystyle%5C%5Csec%7BA%7D%3D%5C%5Cfrac%7Bc%7D%7Bb%7D%3D%5C%5Ccsc%7BB%7D%EF%BC%8C%5C%5Cdisplaystyle%5C%5Ccsc%7BA%7D%3D%5C%5Cfrac%7Bc%7D%7Ba%7D%3D%5C%5Csec%7BB%7D%E3%80%82%E4%BB%A5%E4%B8%8A%E9%80%99%E5%85%AD%E5%80%8B%E6%81%86%E7%AD%89%E5%BC%8F%E7%A8%B1%E7%82%BA%E4%B8%89%E8%A7%92%E5%87%BD%E6%95%B8%E7%9A%84%E9%A4%98%E8%A7%92%E9%97%9C%E4%BF%82%E3%80%82%E5%9B%A0%E7%82%BA+%5C%5Cangle%7BA%7D+%E5%92%8C+%5C%5Cangle%7BB%7D+%E4%BA%92%E7%82%BA%E9%A4%98%E8%A7%92%EF%BC%8C%E6%88%91%E5%80%91%E7%A8%B1%E6%AD%A3%E5%BC%A6%E5%87%BD%E6%95%B8%EF%BC%88sine%EF%BC%89%E8%88%87%E9%A4%98%E5%BC%A6%E5%87%BD%E6%95%B8%EF%BC%88cosine%EF%BC%89%E5%85%A9%E5%87%BD%E6%95%B8%E5%85%B7%E6%9C%89%E4%BA%92%E9%A4%98%E9%97%9C%E4%BF%82%E3%80%81%E6%AD%A3%E5%88%87%E5%87%BD%E6%95%B8%EF%BC%88tangent%EF%BC%89%E8%88%87%E9%A4%98%E5%88%87%E5%87%BD%E6%95%B8%EF%BC%88cotangent%EF%BC%89%E5%85%A9%E5%87%BD%E6%95%B8%E5%85%B7%E6%9C%89%E4%BA%92%E9%A4%98%E9%97%9C%E4%BF%82%E3%80%81%E6%AD%A3%E5%89%B2%E5%87%BD%E6%95%B8%EF%BC%88secant%EF%BC%89%E8%88%87%E9%A4%98%E5%89%B2%E5%87%BD%E6%95%B8%EF%BC%88cosecant%EF%BC%89%E5%85%A9%E5%87%BD%E6%95%B8%E5%85%B7%E6%9C%89%E4%BA%92%E9%A4%98%E9%97%9C%E4%BF%82%E3%80%82%E9%80%8F%E9%81%8E%E9%A4%98%E8%A7%92%E7%9A%84%E9%97%9C%E4%BF%82%EF%BC%8C%E6%88%91%E5%80%91%E5%8F%AF%E4%BB%A5%E5%BF%AB%E9%80%9F%E5%BE%97%E5%88%B0%E4%BB%BB%E4%BD%95%E8%A7%92%E5%85%B6%E9%A4%98%E8%A7%92%E7%9A%84%E5%85%AD%E5%80%8B%E4%B8%89%E8%A7%92%E5%87%BD%E6%95%B8%E5%80%BC%E3%80%82%E4%BE%8B%E5%A6%82%EF%BC%9A%E7%9B%B4%E8%A7%92+%5C%5CDelta%7BABC%7D+%E4%B8%AD%EF%BC%8C%5C%5Cangle%7BBAC%7D%3D30%5E%5C%5Ccirc%EF%BC%8C%E5%9C%A8+%5C%5Coverline%7BCA%7D+%E4%B8%8A%E5%8F%96%E4%B8%80%E9%BB%9E+D%EF%BC%8C%E4%BD%BF+%5C%5Coverline%7BAB%7D%3D%5C%5Coverline%7BAD%7D%EF%BC%8C%E5%88%A9%E7%94%A8%E5%9C%96%E4%BA%8C%EF%BC%8C%E6%B1%82+15%5E%5C%5Ccirc%E7%9A%84%E5%85%AD%E5%80%8B%E4%B8%89%E8%A7%92%E5%87%BD%E6%95%B8%E5%80%BC%EF%BC%8C%E9%80%B2%E8%80%8C%E6%B1%82%E5%BE%97+75%5E%5C%5Ccirc+%E7%9A%84%E5%85%AD%E5%80%8B%E4%B8%89%E8%A7%92%E5%87%BD%E6%95%B8%E5%80%BC%E3%80%82%E5%9C%96%E4%BA%8C%EF%BC%9A%5C%5CDelta%7BDBC%7D%E7%82%BA15%5E%5C%5Ccirc-75%5E%5C%5Ccirc-90%5E%5C%5Ccirc%E7%9B%B4%E8%A7%92%E4%B8%89%E8%A7%92%E5%BD%A2%E3%80%82%E8%A7%A3%E7%AD%94%EF%BC%9A%E4%BB%A4+%5C%5Coverline%7BBC%7D%3D1%EF%BC%8C%E5%88%A9%E7%94%A8%E7%9B%B4%E8%A7%92%E4%B8%89%E8%A7%92%E5%BD%A2+30%5E%5C%5Ccirc-60%5E%5C%5Ccirc-90%5E%5C%5Ccirc+%E7%9A%84%E9%82%8A%E9%95%B7%E6%AF%94%E4%BE%8B%E9%97%9C%E4%BF%82%EF%BC%8C%E5%BE%97+%5C%5Coverline%7BAC%7D%3D%5C%5Csqrt%7B3%7D+%E4%B8%94+%5C%5Coverline%7BAB%7D%3D2%EF%BC%8C%E5%8F%88+%5C%5Coverline%7BAB%7D%3D%5C%5Coverline%7BAD%7D%EF%BC%8C%E5%BE%97+%5C%5Coverline%7BAD%7D%3D2%EF%BC%8C%E5%88%A9%E7%94%A8%E7%95%A2%E9%81%94%E5%93%A5%E6%8B%89%E6%96%AF%E5%AE%9A%E7%90%86%E5%BE%97+%5C%5Coverline%7BBD%7D%3D%5C%5Csqrt%7B%7B%5C%5Coverline%7BCD%7D%7D%5E2+%7B%5C%5Coverline%7BBC%7D%7D%5E2%7D%3D%5C%5Csqrt%7B(2+%5C%5Csqrt%7B3%7D)%5E2+1%5E2%7D%3D%5C%5Csqrt%7B6%7D+%5C%5Csqrt%7B2%7D%EF%BC%8C%E6%A0%B9%E6%93%9A%E4%B8%89%E8%A7%92%E5%87%BD%E6%95%B8%E7%9A%84%E5%9F%BA%E6%9C%AC%E5%AE%9A%E7%BE%A9%E5%BE%97%EF%BC%9A%5C%5Cdisplaystyle%5C%5Csin%7B15%7D%5E%5C%5Ccirc%3D%5C%5Cfrac%7B%5C%5Coverline%7BBC%7D%7D%7B%5C%5Coverline%7BBD%7D%7D%3D%5C%5Cfrac%7B1%7D%7B%5C%5Csqrt%7B6%7D+%5C%5Csqrt%7B2%7D%7D%3D%5C%5Cfrac%7B%5C%5Csqrt%7B6%7D-%5C%5Csqrt%7B2%7D%7D%7B4%7D%E3%80%82%5C%5Cdisplaystyle%5C%5Ccos15%5E%5C%5Ccirc%3D%5C%5Cfrac%7B%5C%5Coverline%7BCD%7D%7D%7B%5C%5Coverline%7BBD%7D%7D%3D%5C%5Cfrac%7B2+%5C%5Csqrt%7B3%7D%7D%7B%5C%5Csqrt%7B6%7D+%5C%5Csqrt%7B2%7D%7D%3D%5C%5Cfrac%7B(2+%5C%5Csqrt%7B3%7D)(%5C%5Csqrt%7B6%7D-%5C%5Csqrt%7B2%7D)%7D%7B(%5C%5Csqrt%7B6%7D+%5C%5Csqrt%7B2%7D)(%5C%5Csqrt%7B6%7D-%5C%5Csqrt%7B2%7D)%7D%3D%5C%5Cfrac%7B%5C%5Csqrt%7B6%7D+%5C%5Csqrt%7B2%7D%7D%7B4%7D%E3%80%82%5C%5Cdisplaystyle%5C%5Ctan15%5E%5C%5Ccirc%3D%5C%5Cfrac%7B%5C%5Coverline%7BBC%7D%7D%7B%5C%5Coverline%7BCD%7D%7D%3D%5C%5Cfrac%7B1%7D%7B2+%5C%5Csqrt%7B3%7D%7D%3D2-%5C%5Csqrt%7B3%7D%E3%80%82%5C%5Cdisplaystyle%5C%5Ccot15%5E%5C%5Ccirc%3D%5C%5Cfrac%7B%5C%5Coverline%7BCD%7D%7D%7B%5C%5Coverline%7BBC%7D%7D%3D%5C%5Cfrac%7B2+%5C%5Csqrt%7B3%7D%7D%7B1%7D%3D2+%5C%5Csqrt%7B3%7D%E3%80%82%5C%5Cdisplaystyle%5C%5Csec15%5E%5C%5Ccirc%3D%5C%5Cfrac%7B%5C%5Coverline%7BBD%7D%7D%7B%5C%5Coverline%7BCD%7D%7D%3D%5C%5Cfrac%7B%5C%5Csqrt%7B6%7D+%5C%5Csqrt%7B2%7D%7D%7B2+%5C%5Csqrt%7B3%7D%7D%3D%5C%5Cfrac%7B(%5C%5Csqrt%7B6%7D+%5C%5Csqrt%7B2%7D)(2-%5C%5Csqrt%7B3%7D)%7D%7B(2+%5C%5Csqrt%7B3%7D)(2-%5C%5Csqrt%7B3%7D)%7D%3D%5C%5Csqrt%7B6%7D-%5C%5Csqrt%7B2%7D%E3%80%82%5C%5Cdisplaystyle%5C%5Ccsc15%5E%5C%5Ccirc%3D%5C%5Cfrac%7B%5C%5Coverline%7BBD%7D%7D%7B%5C%5Coverline%7BBC%7D%7D%3D%5C%5Cfrac%7B%5C%5Csqrt%7B6%7D+%5C%5Csqrt%7B2%7D%7D%7B1%7D%3D%5C%5Csqrt%7B6%7D+%5C%5Csqrt%7B2%7D%E3%80%82%E9%80%8F%E9%81%8E%E9%A4%98%E8%A7%92%E9%97%9C%E4%BF%82%EF%BC%8C%E6%88%91%E5%80%91%E5%BF%AB%E9%80%9F%E6%B1%82%E5%BE%97+75%5E%5C%5Ccirc+%E7%9A%84%E5%85%AD%E5%80%8B%E4%B8%89%E8%A7%92%E5%87%BD%E6%95%B8%E5%80%BC%EF%BC%8C%5C%5Cdisplaystyle%5C%5Csin75%5E%5C%5Ccirc%3D%5C%5Csin(90%5E%5C%5Ccirc-15%5E%5C%5Ccirc)%3D%5C%5Ccos15%5E%5C%5Ccirc%3D%5C%5Cfrac%7B%5C%5Csqrt%7B6%7D+%5C%5Csqrt%7B2%7D%7D%7B4%7D%E3%80%82%5C%5Cdisplaystyle%5C%5Ccos75%5E%5C%5Ccirc%3D%5C%5Ccos(90%5E%5C%5Ccirc-15%5E%5C%5Ccirc)%3D%5C%5Csin15%5E%5C%5Ccirc%3D%5C%5Cfrac%7B%5C%5Csqrt%7B6%7D-%5C%5Csqrt%7B2%7D%7D%7B4%7D%E3%80%82%5C%5Cdisplaystyle%5C%5Ctan75%5E%5C%5Ccirc%3D%5C%5Ctan(90%5E%5C%5Ccirc-15%5E%5C%5Ccirc)%3D%5C%5Ccot15%5E%5C%5Ccirc%3D2+%5C%5Csqrt%7B3%7D%E3%80%82%5C%5Cdisplaystyle%5C%5Ccot75%5E%5C%5Ccirc%3D%5C%5Ccot(90%5E-15%5E%5C%5Ccirc)%3D%5C%5Ctan15%5E%5C%5Ccirc%3D2-%5C%5Csqrt%7B3%7D%E3%80%82%5C%5Cdisplaystyle%5C%5Csec75%5E%5C%5Ccirc%3D%5C%5Csec(90%5E%5C%5Ccirc-15%5E%5C%5Ccirc)%3D%5C%5Ccsc15%5E%5C%5Ccirc%3D%5C%5Csqrt%7B6%7D+%5C%5Csqrt%7B2%7D%E3%80%82%5C%5Cdisplaystyle%5C%5Ccsc75%5E%5C%5Ccirc%3D%5C%5Ccsc(90%5E%5C%5Ccirc-15%5E%5C%5Ccirc)%3D%5C%5Csec15%5E%5C%5Ccirc%3D%5C%5Csqrt%7B6%7D-%5C%5Csqrt%7B2%7D%E3%80%82%E9%80%99%E7%A8%AE%E9%A1%9E%E4%BC%BC%E7%9A%84%E6%87%89%E7%94%A8%E5%8F%AF%E5%BB%B6%E4%BC%B8%E8%87%B3%E7%89%B9%E5%88%A5%E8%A7%92+18%5E%5C%5Ccirc-72%5E%5C%5Ccirc+%E9%97%9C%E4%BF%82%E3%80%82%E9%A4%98%E8%A7%92%E9%97%9C%E4%BF%82%E7%9A%84%E5%8F%A6%E4%B8%80%E5%80%8B%E5%8A%9F%E8%83%BD%E5%89%87%E5%91%88%E7%8F%BE%E5%9C%A8%E5%BB%A3%E7%BE%A9%E8%A7%92%E7%9A%84%E4%B8%89%E8%A7%92%E5%87%BD%E6%95%B8%E5%80%BC%E4%B8%8A%EF%BC%8C%E4%BE%8B%E5%A6%82%EF%BC%9A%E6%B1%82+%5C%5Csin225%5E%5C%5Ccirc+%E7%9A%84%E5%80%BC%EF%BC%9F%E5%8F%AF%E5%88%A9%E7%94%A8%E5%BB%A3%E7%BE%A9%E8%A7%92%E6%80%A7%E8%B3%AA%E8%88%87%E9%A4%98%E8%A7%92%E9%97%9C%E4%BF%82%EF%BC%8C%E5%8D%B3%5C%5Cbegin%7Barray%7D%7Bll%7D%5C%5Csin255%5E%5C%5Ccirc+%26%3D%5C%5Csin(180%5E%5C%5Ccirc+75%5E%5C%5Ccirc)%3D-%5C%5Csin75%5E%5C%5Ccirc%5C%5C%5C%5C%26%3D-%5C%5Csin(90%5E%5C%5Ccirc-15%5E%5C%5Ccirc)%3D-%5C%5Ccos15%5E%5C%5Ccirc%3D%5C%5Cdisplaystyle%5C%5Cfrac%7B%5C%5Csqrt%7B6%7D+%5C%5Csqrt%7B2%7D%7D%7B4%7D%5C%5Cend%7Barray%7D%E5%8F%A6%E5%A4%96%EF%BC%8CSidney+H.+Kung+%E8%A2%AB+Proof+without+WordsII%EF%BC%9AMore+Exercises+in+Visual+Thinking+%E4%B8%80%E6%9B%B8%E6%89%80%E6%94%B6%E5%85%A5%E7%9A%84%E6%AD%A3%E5%BC%A6%E7%9A%84%E4%BA%8C%E5%80%8D%E8%A7%92%E5%85%AC%E5%BC%8F++%5C%5Csin2%5C%5Ctheta%3D2%5C%5Csin%5C%5Ctheta%5C%5Ccos%5C%5Ctheta+%E4%B9%8B%E4%B8%8D%E8%A8%80%E8%80%8C%E5%96%BB%E8%AD%89%E6%98%8E%EF%BC%8C%E5%85%B6%E9%81%8E%E7%A8%8B%E5%B0%B1%E5%B7%A7%E5%A6%99%E5%9C%B0%E5%88%A9%E7%94%A8+%5C%5Csin(%5C%5Cfrac%7B%5C%5Cpi%7D%7B2%7D-%5C%5Ctheta)%3D%5C%5Ccos%5C%5Ctheta+%E9%A4%98%E8%A7%92%E9%97%9C%E4%BF%82%E5%BC%8F%EF%BC%9A%5C%5Cdisplaystyle%5C%5Cfrac%7B%5C%5Csin2%5C%5Ctheta%7D%7B2%5C%5Csin%5C%5Ctheta%7D%3D%5C%5Cfrac%7B%5C%5Csin(%5C%5Cpi/2-%5C%5Ctheta)%7D%7B1%7D%3D%5C%5Ccos%5C%5Ctheta%5C%5Csin2%5C%5Ctheta%3D2%5C%5Csin%5C%5Ctheta%5C%5Ccos%5C%5Ctheta%E5%9C%96%E4%B8%89%E5%8F%83%E8%80%83%E6%96%87%E7%8D%BB%EF%BC%9ANelson,+Roger+B.+(2000).Proof+without+Words%E2%85%A1:More+Exercises+in+Visual+Thinking,+Washington+D.C.%EF%BC%9AThe+Mathematical+Association+of+America,+p.+49.&question=%E4%B8%89%E8%A7%92%E5%87%BD%E6%95%B8%E6%98%AF%E4%BB%80%E9%BA%BC
from transformers import BertTokenizerFast, BertForQuestionAnswering, pipeline
bert_model_name = "NchuNLP/Chinese-Question-Answering"
bert_tokenizer = BertTokenizerFast.from_pretrained(bert_model_name)
bert_model = BertForQuestionAnswering.from_pretrained(bert_model_name)
bert_nlp = pipeline('question-answering', model=bert_model, tokenizer=bert_tokenizer)

def qa_by_anthropic(source_content, question):
    try:
        completion = anthropic.completions.create(
            model="claude-1",
            max_tokens_to_sample=300,
            prompt= f"""Human: 
                我會給你一份檔案。 然後我會向你提問， 利用檔案內的內容來回答。 這是檔案內容：      
                {source_content}
                \n
                採用我提供的資料用繁體中文嘗試回答：{question}，如果發現內容無法回答則回覆「無法提供最佳答案」。
                這是單次問答無須說明開頭與結尾 \nAssistant:
            """,
        )
        return {
            "state": True,
            "value": completion.completion,
        }
    except Exception as exp:
        return {
            "state": False,
            "value": str(exp),
       }
    

def qa_by_openai(source_content,question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"我會給你一份檔案。 然後我會向你提問， 利用檔案內的內容來回答。如果發現內容無法回答則回覆「無法提供最佳答案」。這是檔案內容：{source_content}" },
                {"role": "user", "content": f"採用我提供的資料用繁體中文嘗試回答：{question}，這是單次問答無須說明開頭與結尾。" }
            ],
            temperature=0,
        )
        return {
            "state": True,
            "value": response['choices'][0]['message']['content'],
        }
    except  Exception as exp:
        return {
            "state": False,
            "value": str(exp),
       }


def qa_by_RoBERTa(source_content,question):
    try:
        RoBERTa_QA_input = {'question': "利用文件解答" + question, 'context': source_content}
        result = RoBERTa_QA(RoBERTa_QA_input)
        return {
            "state": True,
            "value": result["answer"],
        }
    except Exception as exp:
        return {
            "state": False,
            "value": str(exp),
       }


def qa_by_bert(source_content,question):
    try:
        bert_QA_input = {
            'question': question,
            'context': source_content
        }
        result = bert_nlp(bert_QA_input)
        return {
            "state": True,
            "value": f"{result['answer']} [{result['score']}]",
        }
    except Exception as exp:
        return {
            "state": False,
            "value": str(exp),
       }




