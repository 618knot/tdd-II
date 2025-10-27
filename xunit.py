class TestResult:
  def __init__(self):
    self.runCount = 0
    self.errorCount = 0
    self.errors = []

  def testStarted(self):
    self.runCount += 1

  def testFailed(self, errors=None):
    self.errorCount += 1

    if errors:
      self.errors.append(errors)

  def summary(self):
    return f"{self.runCount} run, {self.errorCount} failed" + (f"\nErrors: {','.join(self.errors)}" if self.errors else "")

class BrokenTestResult(TestResult):
  def testFailed(self):
    raise Exception

class TestCase:
  def __init__(self, name):
    self.name = name

  def setUp(self):
    pass

  def tearDown(self):
    pass

  def run(self, result):
    result.testStarted()
    try:
      self.setUp()
    except Exception as e:
      result.testFailed(errors=f"{self.__class__.__name__}.setUp -- {e.__class__.__name__}")
      return

    try:
      method = getattr(self, self.name)
      method()
    except Exception as e:
      result.testFailed(errors=f"{self.__class__.__name__}.{self.name} -- {e.__class__.__name__}")
    finally:
      self.tearDown()

class TestSuite:
  def __init__(self):
    self.tests = []

  def add(self, test):
    self.tests.append(test)

  def run(self, result):
    for test in self.tests:
      test.run(result)

  @classmethod
  def fromTestCase(cls, testCase):
    suite = cls()
    for method in dir(testCase):
      if method.startswith("test"):
        suite.add(testCase(method))
    return suite

class WasRun(TestCase):
  def setUp(self):
    self.log = "setUp "

  def testMethod(self):
    self.log += "testMethod "

  def testBrokenMethod(self):
    self.log += "testBrokenMethod "
    raise Exception

  def tearDown(self):
    self.log += "tearDown "

class WasRunSetUpBroken(TestCase):
  def setUp(self):
    self.log = "setUp "
    raise Exception

class TestCaseTest(TestCase):
  def setUp(self):
    self.result = TestResult()

  def testTemplateMethod(self):
    test = WasRun("testMethod")
    test.run(self.result)
    assert test.log == "setUp testMethod tearDown "

  def testResult(self):
    test = WasRun("testMethod")
    test.run(self.result)
    assert self.result.summary() == "1 run, 0 failed"

  def testFailedResult(self):
    test = WasRun("testBrokenMethod")
    test.run(self.result)
    assert self.result.summary() == "1 run, 1 failed\nErrors: WasRun.testBrokenMethod -- Exception"

  def testFailedResultFormatting(self):
    self.result.testStarted()
    self.result.testFailed()
    assert self.result.summary() == "1 run, 1 failed"

  def testSuite(self):
    suite = TestSuite()
    suite.add(WasRun("testMethod"))
    suite.add(WasRun("testBrokenMethod"))
    suite.run(self.result)
    assert self.result.summary() == "2 run, 1 failed\nErrors: WasRun.testBrokenMethod -- Exception"

  def testTearDownOnBrokenMethod(self):
    test = WasRun("testBrokenMethod")
    test.run(self.result)
    assert test.log == "setUp testBrokenMethod tearDown "

  def testTearDownOnBrokenTestFailed(self):
    self.result = BrokenTestResult()
    test = WasRun("testBrokenMethod")
    try:
      test.run(self.result)
    except Exception:
      assert test.log == "setUp testBrokenMethod tearDown "

  def testTearDownOnBrokenSetUp(self):
    test = WasRunSetUpBroken("testMethod")
    test.run(self.result)
    assert self.result.summary() == "1 run, 1 failed\nErrors: WasRunSetUpBroken.setUp -- Exception"

  def testSuiteFromTestCase(self):
    suite = TestSuite.fromTestCase(WasRun)
    result = TestResult()
    suite.run(result)
    assert result.summary() == "2 run, 1 failed\nErrors: WasRun.testBrokenMethod -- Exception"

if __name__ == "__main__":
  suite = TestSuite.fromTestCase(TestCaseTest)
  result = TestResult()
  suite.run(result)
  print(result.summary())
