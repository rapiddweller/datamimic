Output docs/assets/build-ready.gif
Set Shell bash
Set FontSize 18
Set Width 1100
Set Height 620
Set TypingSpeed 40ms
Hide
Type "cd tests_ce/scenarios/s50_readme_shop && clear" Enter
Show
Type "cat datamimic.xml" Enter
Sleep 4s
Type "datamimic authoring build . | jq '{outcome, replay: .verification.deterministic_replay.status}'" Enter
Sleep 5s
Type "sed -i.bak 's/script=\"parent.id\"/type=\"int\" min=\"100\" max=\"200\"/' datamimic.xml" Enter
Type "datamimic authoring build . | jq '{outcome, first: .diagnostics | map(select(.severity==\"error\")) | .[0].code}'" Enter
Sleep 5s
Type "mv datamimic.xml.bak datamimic.xml && datamimic run datamimic.xml > /dev/null 2>&1; head -4 output/*/customers.csv output/*/orders.csv" Enter
Sleep 6s
