__author__ = 'svyrydenko'

import datetime
import os
import unittest
import unittest.mock
import requests.exceptions
from collections import Counter
import OhtApi2

class StateHolder:
    pass

holder = StateHolder()

class Test_URLCheckSandbox(unittest.TestCase):
    def setUp(self):
        self.obj = OhtApi2.OhtApi("a","b", True)
        self.method = self.obj.set_sandbox_url

    def tearDown(self):
        del self.obj

    def test_URL_check_no_schema(self):
        with self.assertRaises(requests.exceptions.ConnectionError):
            self.method("some.undefined.com")

    def test_URL_check(self):
        with self.assertRaises(requests.exceptions.ConnectionError):
            self.method("https://some.undefined.com")

    def test_valid_URL(self):
        self.assertTrue(self.method("http://sandbox.onehourtranslation.com/api/2"))

    def test_valid_URL_no_schema(self):
        self.assertTrue(self.method("sandbox.onehourtranslation.com/api/2"))


class Test_URLCheckProduct(Test_URLCheckSandbox):
    def setUp(self):
        self.obj = OhtApi2.OhtApi("a","b", False)
        self.method = self.obj.set_base_url


class Test_JsonToObject(unittest.TestCase):
    def setUp(self):
        self.obj = OhtApi2.OhtApi("a","b", True)

    def tearDown(self):
        del self.obj

    def test_jsonToObjectOkAnswer(self):
        good_answer = '{"status":{"code":0,"msg":"ok"},"results":{"project_id":"807837","project_type":"Translation","project_status":"Being translated","project_status_code":"signed","source_language":"en-us","target_language":"ru-ru","resources":{"sources":["rsc-560a693ccfbbc2-86754957","rsc-560a6a5524b4a2-38348001"],"translations":["rsc-560abb5ab099b0-90175867","rsc-560abb5ab4ab73-60700513"],"proofs":"","transcriptions":""},"wordcount":"5","custom":"","resource_binding":{"rsc-560a693ccfbbc2-86754957":["rsc-560abb5ab099b0-90175867"],"rsc-560a6a5524b4a2-38348001":["rsc-560abb5ab4ab73-60700513"],"rsc-560abb5ab099b0-90175867":null,"rsc-560abb5ab4ab73-60700513":null},"linguist_uuid":"70f6df63-9359-4f5b-a7c2-2483123a269a"},"errors":[]}'
        res = self.obj.json_to_ntuple(good_answer)
        self.assertTrue(hasattr(res, "status"), "No attribute <status> in result namedtuple" )
        self.assertTrue(hasattr(res, "results"), "No attribute <results> in result namedtuple" )
        self.assertTrue(hasattr(res, "errors"), "No attribute <errors> in result namedtuple" )

    def test_jsonToObjectErrorAnswer(self):
        bad_answer = '{sdfsdf:{"sd":8}'
        with self.assertRaises(ValueError, msg = "no exception while parse wrong json string"):
            self.obj.json_to_ntuple(bad_answer)


class Test_Answers(unittest.TestCase):
    def setUp(self):
        self.obj = OhtApi2.OhtApi(os.environ['PubKey'],os.environ['PrivKey'], True)
        self.ohtTupleType = "oht_response"
        self.listType = type([]).__name__


    def tearDown(self):
        del self.obj

    def checkAnswerStructure(self, answer, resultExpectedType = type([]).__name__):
        return hasattr(answer, "status") and type(answer.status).__name__ == self.ohtTupleType and \
               hasattr(answer, "results") and type(answer.results).__name__ == resultExpectedType and \
               hasattr(answer, "errors") and type(answer.errors).__name__ == self.listType

    def checkAnswerStatus(self, answer):
        return answer.status.code == 0 and answer.status.msg == 'ok' and not answer.errors

    def validateAnswer(self, answer, resultExpectedType=type([]).__name__):
        self.assertTrue(self.checkAnswerStructure(answer, resultExpectedType), msg="wrong answer structure: "+ str(answer))
        self.assertTrue(self.checkAnswerStatus(answer), msg="status " + str(answer.status))

    def time_format(self):
        return "%Y-%m-%d %H:%M-%S"

class Test_OHTRequestsSimple(Test_Answers):

    def test_supported_language_pairs(self):
        answer = self.obj.supported_language_pairs()
        self.validateAnswer(answer)

    def test_supported_languages(self):
        answer = self.obj.supported_languages()
        self.validateAnswer(answer)

    def test_expertises(self):
        answer = self.obj.expertises()
        self.validateAnswer(answer)

    def test_account_details(self):
        answer = self.obj.account_details()
        self.validateAnswer(answer, resultExpectedType=self.ohtTupleType)

    def test_machine_detectLang(self):
        text = "Next the custom functions are defined on the prototype"
        answer = self.obj.machine_detect_lang(text)
        self.validateAnswer(answer, resultExpectedType=self.ohtTupleType)
        self.assertTrue(answer.results.language == "English", msg="language != 'English' as aspect")

    def test_machine_translate(self):
        text_en = "The sun is shining brightly"
        text_fr = "Le soleil brille de mille feux"

        answer = self.obj.machine_translate("en-us", "fr-fr", text_en)
        self.validateAnswer(answer, resultExpectedType=self.ohtTupleType)
        self.assertTrue(text_fr == answer.results.TranslatedText, msg="Translate test wrong: " + answer.results.TranslatedText)


class Test_OHTRequestsProject(Test_Answers):

    def get_fake_translated_resource(self):
        try:
            uuid = holder.trunslated_resource
        except:
            holder.content_translated = "Le soleil brille de mille feux"
            holder.resource_name_translated = "test_some_name"

            answer = self.obj.create_file_resource(file_name=holder.resource_name_translated, file_content=holder.content_translated)
            self.validateAnswer(answer)
            self.assertTrue(len(answer.results) != 0)

            holder.trunslated_resource = answer.results
            uuid = holder.trunslated_resource

        return uuid


    def get_file_resource(self):
        try:
            uuid = holder.currentResource
            count_words = holder.count_words
        except:
            holder.content = "The sun is shining brightly"
            holder.resource_name = "test_some_name"

            answer = self.obj.create_file_resource(file_name=holder.resource_name, file_content=holder.content)
            self.validateAnswer(answer)
            self.assertTrue(len(answer.results) != 0)

            counter = Counter()
            counter.update(holder.content.split())

            holder.currentResource = answer.results
            uuid = holder.currentResource

            holder.count_words = sum(counter.values())
            count_words = holder.count_words

        return uuid, count_words

    def test_create_file_resource(self):
        """ Testing only upload content """
        uuids = self.get_file_resource()
        self.assertTrue(len(uuids) != 0)

    def test_word_count(self):
        uuid_list, count = self.get_file_resource()
        answer = self.obj.word_count(uuid_list)
        self.validateAnswer(answer, resultExpectedType=self.ohtTupleType)
        self.assertTrue(answer.results.resources[0].wordcount == count)
        self.assertTrue(answer.results.resources[0].resource == uuid_list[0])

    def test_get_resource(self):
        content_base64 = 'VGhlIHN1biBpcyBzaGluaW5nIGJyaWdodGx5'
        uuid_list = self.get_file_resource()[:1][0]
        answer = self.obj.get_resource(resource_uuid=uuid_list[0], fetch="base64")
        self.validateAnswer(answer, resultExpectedType=self.ohtTupleType)
        self.assertTrue(answer.results.type == "file")
        self.assertTrue(answer.results.file_name == holder.resource_name)
        self.assertTrue(len(answer.results.download_url))
        self.assertTrue(answer.results.content == content_base64)

    def test_download_resource(self):
        uuid_list = self.get_file_resource()[:1][0]
        answer = self.obj.download_resource(uuid_list[0])
        self.assertTrue(len(answer) > 0)
        self.assertTrue(answer == holder.content)

    def test_quote(self):
        uuid_list = self.get_file_resource()[:1][0]
        answer = self.obj.quote(uuid_list, "en-us", "fr-fr", service="translation", expertise="marketing-consumer-media", proofreading="1", currency='EUR')
        self.validateAnswer(answer, resultExpectedType=self.ohtTupleType)
        self.assertTrue(answer.results.resources[0].resource == uuid_list[0])
        self.assertTrue(answer.results.resources[0].wordcount == holder.count_words)
        self.assertTrue(answer.results.total.wordcount == holder.count_words)
        self.assertTrue(answer.results.currency =="EUR")

    def get_translation_project_id(self):
        """ expertise parameter is optional, but under sandbox it's required """

        # return 807896
        try:
            project_id = holder.translation_project_id
        except:
            uuid_list = self.get_file_resource()[:1][0]

            # sandbox create translation project for languages pair 'en-us' - 'fr-fr' (only one supported)
            # also need pass not empty expertise
            name = "unittest translate_project " + datetime.datetime.now().strftime(self.time_format())
            answer = self.obj.create_translation_project("en-us", "fr-fr", uuid_list, name=name, expertise="marketing-consumer-media")
            self.validateAnswer(answer, resultExpectedType=self.ohtTupleType)
            holder.translation_project_id = answer.results.project_id
            project_id = holder.translation_project_id

        return project_id

    def test_create_translation_project(self):
        project_id = self.get_translation_project_id()
        self.assertTrue(project_id != 0)

    def test_project_detail(self):
        project_id = self.get_translation_project_id()
        answer = self.obj.project_detail(project_id)
        self.validateAnswer(answer, resultExpectedType=self.ohtTupleType)
        self.assertTrue(answer.results.project_id == str(project_id))
        holder.translations = answer.results.resources.translations

    def test_wait_cancel_project(self):
        """ No testing status - in sandbox cancel project is ok wright after creating """
        project_id = self.get_translation_project_id()
        answer = self.obj.cancel_project(project_id)
        self.assertTrue(self.checkAnswerStructure(answer), msg="answer = " + str(answer))

    def test_project_comments(self):
        project_id = self.get_translation_project_id()
        answer = self.obj.project_comments(project_id)
        self.validateAnswer(answer)

    def test_post_comment(self):
        project_id = self.get_translation_project_id()
        text = "new comment " + datetime.datetime.now().strftime(self.time_format())
        answer = self.obj.post_comment(project_id, text)
        self.validateAnswer(answer)

    def test_project_ratings(self):
        project_id = self.get_translation_project_id()
        answer = self.obj.project_ratings(project_id)
        self.validateAnswer(answer)

    def test_post_project_ratings(self):
        """ Only check answer structure - under sandbox this method
            always return 'forbidden - you are not allowed to perform this request' (code=102)
        """
        project_id = self.get_translation_project_id()
        answer = self.obj.post_project_ratings(project_id, "Customer", 1, remarks="remarks")
        self.validateAnswer(answer)
        self.assertTrue(self.checkAnswerStructure(answer), msg="answer = " + str(answer))

    def test_create_proof_reading_project(self):
        """ there is no expertise parameter in docs, but under sandbox it's required """
        uuid_list = self.get_file_resource()[:1][0]
        language = "en-us"
        name = "unittest proof_reading_project " + datetime.datetime.now().strftime(self.time_format())
        answer = self.obj.create_proof_reading_project(language, uuid_list, name=name, expertise="marketing-consumer-media")
        self.validateAnswer(answer, resultExpectedType=self.ohtTupleType)
        self.assertTrue(answer.results.project_id != 0)

    def test_wait_create_proof_translated_project(self):
        """ expertise parameter is optional, but under sandbox it's required """
        source_uuid_list = self.get_file_resource()[:1][0]
        language_source = "en-us"
        language_target = "fr-fr"
        name = "unittest proof_translated " + datetime.datetime.now().strftime(self.time_format())
        # translations_uuid_list = holder.translations
        translations_uuid_list = self.get_fake_translated_resource()
        self.assertTrue(translations_uuid_list, msg="No translations uuid yet")
        self.assertTrue(type(translations_uuid_list) == type([]))
        self.assertTrue(len(translations_uuid_list) > 0)
        answer = self.obj.create_proof_translated_project(language_source, language_target, source_uuid_list, translations_uuid_list, expertise="marketing-consumer-media", name=name)
        self.validateAnswer(answer, resultExpectedType=self.ohtTupleType)
        self.assertTrue(answer.results.project_id != 0)

    def test_create_transcription_project(self):
        uuid_list = self.get_file_resource()[:1][0]
        language = "en-us"
        name = "unittest transcription_project " + datetime.datetime.now().strftime(self.time_format())
        answer = self.obj.create_transcription_project(language, uuid_list, name=name)
        self.validateAnswer(answer, resultExpectedType=self.ohtTupleType)
        self.assertTrue(answer.results.project_id != 0)


if __name__ == '__main__':
    unittest.main()