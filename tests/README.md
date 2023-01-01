### Unit tests

Unit tests are written using the standard Python unittest module.

Tests are written using the Arrange/Act/Assert pattern, where the test data is first set up,
then the actual call to the code is made, and finally the assertion is tested.

For example:

```python
def test_when_bIsActive_is_true_then_state_bIsActive_true(self):
    "Check that the bIsActive is correctly set to true"

    self.raw_json["bIsActive"] = 1

    genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

    self.assertTrue(genius_zone.data["_state"]["bIsActive"])
```
Here, the first line arranges the test data, setting the value in the raw JSON that we want to test the parsing of.

The intention is to limit this to setting up any data that has a direct impact on what the unit test is specifically testing. You'll see at the top of our test files that we set up the raw json with all the data needed to not fail to be parsed. In this example, we only need to set the bIsActive field on the JSON for this test, as that is the value that we are testing the parsing of.

The second line is acting, i.e. this is calling the code to test. In this example, this creates an instance of the GeniusZone class, which automatically parses the raw JSON passed in to the contructor.

The third line is asserting whether the tested property contains the expected value.

```python
def test_when_iType_OnOffTimer_fSP_not_zero_setpoint_state_setpoint_set_true(self):
    """Check that the setpoint is set to true when iType is OnOffTimer

    and fSP is not zero"""

    self.raw_json["fSP"] = 1.0
    self.raw_json["iType"] = ZONE_TYPE.OnOffTimer

    genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

    self.assertTrue(genius_zone.data["setpoint"])
```
In this example, the first two lines are setting up the data fields that are required for the test. Specifically,
it sets the iType of the zone for this specific test case, then the value of fSP that is parsed. Both these values
are required to be able to test the desired code branch.

```python
def test_when_iType_should_set_setpoint_state_setpoint_set_correctly(self):
    "Check that the setpoint is set for certain values of iType"

    setpoint = 21.0
    self.raw_json["fSP"] = setpoint

    test_values = (
        ZONE_TYPE.ControlSP,
        ZONE_TYPE.TPI
    )

    for zone_type in test_values:
        with self.subTest(zone_type=zone_type):
            self.raw_json["iType"] = zone_type

            genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

            self.assertEqual(genius_zone.data["setpoint"], setpoint)
```
In this more complicated example, we want to test that a specific value of the raw JSON field
is successfully parsed, for a range of values of a separate field in the JSON. To do this, we are using
sub-tests, which creates a test for each value in the test_values tuple.
The arrange section here sets up a local variable for the setpoint, as this will be used to set the value on the JSON
and to assert whether that value has been successfully parsed.
The test values that will change for each sub-test are then set up, looped over, and a sub-test created. Within this sub-test, there are its own arrange, act, and assert sections.

To manually run the tests from the command line, use this command:
```
python -m unittest discover -p "*_test.py"
```

Where the code to be tested contains other classes, make use of the Mock module to mock up
these classes and any behaviours that you require for your tests.

The idea is to test as little as possible in each test. To this aim, do not use multiple
asserts in a unit test.
