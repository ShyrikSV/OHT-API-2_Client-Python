__author__ = 'svyrydenko'

import unittest
import requests.exceptions
import OhtApi2

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
        self.obj = OhtApi2.OhtApi("secret","secret", True)
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

class Test_OHTRequestsSimple(Test_Answers):

    def test_supported_language_pairs(self):
        answer = self.obj.supported_language_pairs()
        self.assertTrue(self.checkAnswerStructure(answer))
        self.assertTrue(self.checkAnswerStatus(answer))

    def test_supported_languages(self):
        answer = self.obj.supported_languages()
        self.assertTrue(self.checkAnswerStructure(answer))
        self.assertTrue(self.checkAnswerStatus(answer))

    def test_expertises(self):
        answer = self.obj.expertises()
        self.assertTrue(self.checkAnswerStructure(answer))
        self.assertTrue(self.checkAnswerStatus(answer))

    def test_account_details(self):
        answer = self.obj.account_details()
        self.assertTrue(self.checkAnswerStructure(answer, self.ohtTupleType))
        self.assertTrue(self.checkAnswerStatus(answer))

    def test_machine_detectLang(self):
        text = "Next the custom functions are defined on the prototype"
        answer = self.obj.machine_detect_lang(text)
        self.assertTrue(self.checkAnswerStructure(answer, self.ohtTupleType))
        self.assertTrue(answer.results.language == "English")
        self.assertTrue(self.checkAnswerStatus(answer))


if __name__ == '__main__':
    unittest.main()