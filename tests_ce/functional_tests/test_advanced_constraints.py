    def test_multi_level_filtering_chain(self):
        """
        Test chain of filtering constraints across multiple levels.

        This test validates that multiple levels of filtering work correctly in sequence,
        with each level building on the results of the previous level.
        """
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_multi_level_filtering.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        # Verify results from multi-level filtering
        filtering_result = result["multi_level_filtering"]
        self.assertEqual(len(filtering_result), 1)

        # Final filtered results should only have customers that match all criteria
        final_approved = filtering_result[0]["final_approved"]
        self.assertGreater(len(final_approved), 0)

        # Check final filtered customers meet all criteria
        for customer in final_approved:
            # Should be high income with low risk profile and approved status
            self.assertGreaterEqual(customer["income"], 75000)
            self.assertEqual(customer["risk_profile"], "Low")
            self.assertEqual(customer["approval_status"], "Approved") 