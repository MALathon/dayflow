"""Test HTML to Markdown conversion with real-world examples."""

from dayflow.core.graph_client import GraphAPIClient
from dayflow.core.html_to_markdown import html_to_markdown


class TestRealWorldHTMLConversion:
    """Test HTML to Markdown conversion with actual examples from the user's calendar."""

    def test_s1_review_meeting_html(self):
        """Test converting the exact HTML from the S1 review meeting example."""
        # This is the actual HTML content from the user's example
        html = """<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<meta name="Generator" content="Microsoft Word 15 (filtered medium)">
<style>
<!--
@font-face
    {font-family:Wingdings}
@font-face
    {font-family:"Cambria Math"}
@font-face
    {font-family:Aptos}
@font-face
    {font-family:"Segoe UI"}
p.MsoNormal, li.MsoNormal, div.MsoNormal
    {margin:0in;
    font-size:12.0pt;
    font-family:"Aptos",sans-serif}
a:link, span.MsoHyperlink
    {color:#467886;
    text-decoration:underline}
p.MsoListParagraph, li.MsoListParagraph, div.MsoListParagraph
    {margin-top:0in;
    margin-right:0in;
    margin-bottom:0in;
    margin-left:.5in;
    font-size:12.0pt;
    font-family:"Aptos",sans-serif}
span.me-email-text
    {}
span.me-email-text-secondary
    {}
span.me-email-headline
    {}
span.EmailStyle22
    {}
.MsoChpDefault
    {font-size:10.0pt}
@page WordSection1
    {margin:1.0in 1.0in 1.0in 1.0in}
div.WordSection1
    {}
ol
    {margin-bottom:0in}
ul
    {margin-bottom:0in}
-->
</style>
</head>
<body lang="EN-US" link="#467886" vlink="#96607D" style="word-wrap:break-word">
<div class="WordSection1">
<p class="MsoNormal">S1 review of projects coming out of the Intake process. Documentation to be sent 1 week in advance for review.</p>
<p class="MsoNormal">&nbsp;</p>
<p class="MsoNormal">Agenda:</p>
<ul type="disc" style="margin-top:0in">
<li class="MsoListParagraph" style="margin-left:0in">AIA to present the findings of their technical S1 evaluation</li><li class="MsoListParagraph" style="margin-left:0in">Stakeholders provide feedback.</li></ul>
<p class="MsoNormal">&nbsp;</p>
<p class="MsoNormal">Requested feedback from this group</p>
<ol start="1" type="1" style="margin-top:0in">
<li class="MsoNormal" style="">Provide an opinion: Is this the right team &amp; right time to move forward with this project (technically speaking)</li><li class="MsoNormal" style="">Review the resources identified and revise based on their knowledge of other projects at Mayo. Discuss alignment with existing Mayo architecture / capabilities</li><li class="MsoNormal" style="">Recommend which IT team &amp; Org Home is best suited to develop this beyond an AIA Prototype.</li></ol>
<p class="MsoNormal">&nbsp;</p>
<div>
<div style="margin-bottom:.25in; overflow:hidden">
<p class="MsoNormal"><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">________________________________________________________________________________</span><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424"></span></p>
</div>
<div style="margin-bottom:9.0pt">
<p class="MsoNormal"><span class="me-email-text"><b><span style="font-size:18.0pt; font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">Microsoft Teams</span></b></span><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">
<a href="https://nam12.safelinks.protection.outlook.com/?url=https%3A%2F%2Faka.ms%2FJoinTeamsMeeting%3Fomkt%3Den-US&amp;data=05%7C02%7CLifson.Mark%40mayo.edu%7C5be99784a6f84057179708dd7dde1599%7Ca25fff9c3f634fb29a8ad9bdd0321f9a%7C0%7C0%7C638805114974320823%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&amp;sdata=Ez2%2F8xhXOIZQaO7yi9JgjbQcxqLvIKztLYV3JnmAJwk%3D&amp;reserved=0" originalsrc="https://aka.ms/JoinTeamsMeeting?omkt=en-US">
<span style="font-size:10.5pt; color:#5B5FC7">Need help?</span></a> </span></p>
</div>
<div style="margin-bottom:4.5pt">
<p class="MsoNormal"><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424"><a href="https://nam12.safelinks.protection.outlook.com/ap/t-59584e83/?url=https%3A%2F%2Fteams.microsoft.com%2Fl%2Fmeetup-join%2F19%253ameeting_MDlkZmFhZmItNzk2Mi00ODQzLWJjNjUtNWE0ZGY2Y2YxNTZj%2540thread.v2%2F0%3Fcontext%3D%257b%2522Tid%2522%253a%2522a25fff9c-3f63-4fb2-9a8a-d9bdd0321f9a%2522%252c%2522Oid%2522%253a%2522f3356392-79ac-4703-829f-9810d7f76599%2522%257d&amp;data=05%7C02%7CLifson.Mark%40mayo.edu%7C5be99784a6f84057179708dd7dde1599%7Ca25fff9c3f634fb29a8ad9bdd0321f9a%7C0%7C0%7C638805114974334461%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&amp;sdata=JyZpqeoTD6WTEYrYedAipv1iz4FuisbYYrKeFF%2BMjjw%3D&amp;reserved=0" originalsrc="https://teams.microsoft.com/l/meetup-join/19%3ameeting_MDlkZmFhZmItNzk2Mi00ODQzLWJjNjUtNWE0ZGY2Y2YxNTZj%40thread.v2/0?context=%7b%22Tid%22%3a%22a25fff9c-3f63-4fb2-9a8a-d9bdd0321f9a%22%2c%22Oid%22%3a%22f3356392-79ac-4703-829f-9810d7f76599%22%7d" title="Meeting join link"><b><span style="font-size:15.0pt; color:#5B5FC7">Join
 the meeting now</span></b></a> </span></p>
</div>
<div style="margin-bottom:4.5pt">
<p class="MsoNormal"><span class="me-email-text-secondary"><span style="font-size:10.5pt; font-family:&quot;Segoe UI&quot;,sans-serif; color:#616161">Meeting ID:
</span></span><span class="me-email-text"><span style="font-size:10.5pt; font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">293 451 842 702</span></span><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">
</span></p>
</div>
<div style="margin-bottom:.25in">
<p class="MsoNormal"><span class="me-email-text-secondary"><span style="font-size:10.5pt; font-family:&quot;Segoe UI&quot;,sans-serif; color:#616161">Passcode:
</span></span><span class="me-email-text"><span style="font-size:10.5pt; font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">AJ3Yg2C6</span></span><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">
</span></p>
</div>
<div style="margin-bottom:.25in">
<div class="MsoNormal" align="center" style="text-align:center"><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">
<hr size="1" width="100%" align="center">
</span></div>
</div>
<div>
<div style="margin-bottom:4.5pt">
<p class="MsoNormal"><span class="me-email-text"><b><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">Dial in by phone</span></b></span><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">
</span></p>
</div>
<div style="margin-bottom:4.5pt">
<p class="MsoNormal"><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424"><a href="tel:+15072181590,,719224215"><span style="font-size:10.5pt; color:#5B5FC7">+1 507-218-1590,,719224215#</span></a>
</span><span class="me-email-text"><span style="font-size:10.5pt; font-family:&quot;Segoe UI&quot;,sans-serif; color:#616161">United States, Rochester</span></span><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">
</span></p>
</div>
<div style="margin-bottom:4.5pt">
<p class="MsoNormal"><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424"><a href="https://nam12.safelinks.protection.outlook.com/?url=https%3A%2F%2Fdialin.teams.microsoft.com%2F8840639d-8470-4be5-887f-3427fe16a023%3Fid%3D719224215&amp;data=05%7C02%7CLifson.Mark%40mayo.edu%7C5be99784a6f84057179708dd7dde1599%7Ca25fff9c3f634fb29a8ad9bdd0321f9a%7C0%7C0%7C638805114974345286%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&amp;sdata=AlDrkpq4%2BRmCAVJshwJnI4dmzlUv6chUMtubNR0ZP7s%3D&amp;reserved=0" originalsrc="https://dialin.teams.microsoft.com/8840639d-8470-4be5-887f-3427fe16a023?id=719224215"><span style="font-size:10.5pt; color:#5B5FC7">Find
 a local number</span></a> </span></p>
</div>
</div>
<div style="margin-bottom:.25in">
<p class="MsoNormal"><span class="me-email-text-secondary"><span style="font-size:10.5pt; font-family:&quot;Segoe UI&quot;,sans-serif; color:#616161">Phone conference ID:
</span></span><span class="me-email-text"><span style="font-size:10.5pt; font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">719 224 215#</span></span><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">
</span></p>
</div>
<div style="margin-bottom:4.5pt">
<p class="MsoNormal"><span class="me-email-headline"><b><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">Join on a video conferencing device</span></b></span><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">
</span></p>
</div>
<div style="margin-bottom:4.5pt">
<p class="MsoNormal"><span class="me-email-text"><span style="font-size:10.5pt; font-family:&quot;Segoe UI&quot;,sans-serif; color:#616161">Tenant key:
</span></span><span class="me-email-text"><span style="font-size:10.5pt; font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424"><a href="mailto:522621028@t.plcm.vc">522621028@t.plcm.vc</a></span></span><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">
</span></p>
</div>
<div style="margin-bottom:4.5pt">
<p class="MsoNormal"><span class="me-email-text-secondary"><span style="font-size:10.5pt; font-family:&quot;Segoe UI&quot;,sans-serif; color:#616161">Video ID:
</span></span><span class="me-email-text"><span style="font-size:10.5pt; font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">114 301 628 4</span></span><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">
</span></p>
</div>
<div style="margin-bottom:.25in">
<p class="MsoNormal"><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424"><a href="https://nam12.safelinks.protection.outlook.com/?url=https%3A%2F%2Fdialin.plcm.vc%2Fteams%2F%3Fkey%3D522621028%26conf%3D1143016284&amp;data=05%7C02%7CLifson.Mark%40mayo.edu%7C5be99784a6f84057179708dd7dde1599%7Ca25fff9c3f634fb29a8ad9bdd0321f9a%7C0%7C0%7C638805114974354100%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&amp;sdata=QNPSPXYX%2BO0vZpkQAaMJAuW996Z3MbZHIJR1e0MJ60A%3D&amp;reserved=0" originalsrc="https://dialin.plcm.vc/teams/?key=522621028&amp;conf=1143016284"><span style="font-size:10.5pt; color:#5B5FC7">More
 info</span></a> </span></p>
</div>
<div>
<p class="MsoNormal"><span class="me-email-text-secondary"><span style="font-size:10.5pt; font-family:&quot;Segoe UI&quot;,sans-serif; color:#616161">For organizers:
</span></span><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424"><a href="https://nam12.safelinks.protection.outlook.com/?url=https%3A%2F%2Fteams.microsoft.com%2FmeetingOptions%2F%3ForganizerId%3Df3356392-79ac-4703-829f-9810d7f76599%26tenantId%3Da25fff9c-3f63-4fb2-9a8a-d9bdd0321f9a%26threadId%3D19_meeting_MDlkZmFhZmItNzk2Mi00ODQzLWJjNjUtNWE0ZGY2Y2YxNTZj%40thread.v2%26messageId%3D0%26language%3Den-US&amp;data=05%7C02%7CLifson.Mark%40mayo.edu%7C5be99784a6f84057179708dd7dde1599%7Ca25fff9c3f634fb29a8ad9bdd0321f9a%7C0%7C0%7C638805114974362661%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&amp;sdata=v1Ij1%2BakncOD9L54HKXVf4ktJ4IdbOkUI2ORulp5DGw%3D&amp;reserved=0" originalsrc="https://teams.microsoft.com/meetingOptions/?organizerId=f3356392-79ac-4703-829f-9810d7f76599&amp;tenantId=a25fff9c-3f63-4fb2-9a8a-d9bdd0321f9a&amp;threadId=19_meeting_MDlkZmFhZmItNzk2Mi00ODQzLWJjNjUtNWE0ZGY2Y2YxNTZj@thread.v2&amp;messageId=0&amp;language=en-US"><span style="font-size:10.5pt; color:#5B5FC7">Meeting
 options</span></a> </span><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#D1D1D1">|</span><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">
<a href="https://nam12.safelinks.protection.outlook.com/?url=https%3A%2F%2Fdialin.teams.microsoft.com%2Fusp%2Fpstnconferencing&amp;data=05%7C02%7CLifson.Mark%40mayo.edu%7C5be99784a6f84057179708dd7dde1599%7Ca25fff9c3f634fb29a8ad9bdd0321f9a%7C0%7C0%7C638805114974371410%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&amp;sdata=KET3uLKecPhRaWqrrYV6aLqmK8RZqRDnu8Eo0IzMhpk%3D&amp;reserved=0" originalsrc="https://dialin.teams.microsoft.com/usp/pstnconferencing">
<span style="font-size:10.5pt; color:#5B5FC7">Reset dial-in PIN</span></a> </span>
</p>
</div>
<div style="margin-bottom:.25in; overflow:hidden">
<p class="MsoNormal"><span style="font-family:&quot;Segoe UI&quot;,sans-serif; color:#242424">________________________________________________________________________________</span></p>
</div>
</div>
<p class="MsoNormal">&nbsp;</p>
</div>
</body>
</html>"""

        # Convert HTML to Markdown
        result = html_to_markdown(html)

        # Core content should be preserved
        assert "S1 review of projects coming out of the Intake process" in result
        assert "Documentation to be sent 1 week in advance for review" in result
        assert "Agenda:" in result
        assert (
            "- AIA to present the findings of their technical S1 evaluation" in result
        )
        assert "- Stakeholders provide feedback." in result
        assert "Requested feedback from this group" in result
        assert (
            "1. Provide an opinion: Is this the right team & right time to move forward with this project (technically speaking)"
            in result
        )
        assert (
            "1. Review the resources identified and revise based on their knowledge of other projects at Mayo"
            in result
        )
        assert (
            "1. Recommend which IT team & Org Home is best suited to develop this beyond an AIA Prototype"
            in result
        )

        # All style content should be removed
        assert "@font-face" not in result
        assert "font-family:" not in result
        assert "Wingdings" not in result
        assert "Cambria Math" not in result
        assert "Aptos" not in result
        assert "Segoe UI" not in result
        assert "margin:0in" not in result
        assert "font-size:12.0pt" not in result
        assert ".MsoNormal" not in result
        assert ".MsoListParagraph" not in result
        assert "style=" not in result
        assert "<style>" not in result
        assert "</style>" not in result

        # HTML tags should be removed
        assert "<p" not in result
        assert "</p>" not in result
        assert "<div" not in result
        assert "</div>" not in result
        assert "<span" not in result
        assert "</span>" not in result
        assert "class=" not in result

        # A Teams-related link should be present (may be wrapped in protection URL)
        assert "teams.microsoft.com" in result or "Join" in result

        # Meeting ID and Passcode should be removed
        assert "293 451 842 702" not in result  # Meeting ID numbers removed
        assert "AJ3Yg2C6" not in result  # Passcode removed
        assert "719 224 215#" not in result  # Phone conference ID removed
        assert "114 301 628 4" not in result  # Video ID removed
        assert "522621028@t.plcm.vc" not in result  # Tenant key removed

        # Verify no excessive whitespace
        assert "\n\n\n" not in result  # No triple newlines
        assert "   " not in result  # No triple spaces

    def test_graph_api_integration_with_complex_html(self):
        """Test the full pipeline from Graph API to clean Markdown."""
        client = GraphAPIClient("mock-token")

        # Create event with complex HTML like the user's example
        raw_event = {
            "id": "event123",
            "subject": "S1 review of AIA projects",
            "start": {"dateTime": "2025-07-03T18:00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2025-07-03T19:00:00", "timeZone": "UTC"},
            "location": {"displayName": "Microsoft Teams Meeting"},
            "body": {
                "contentType": "HTML",
                "content": """<html><head><style>@font-face{font-family:Aptos}</style></head>
                <body><p>S1 review of projects</p>
                <ul><li>AIA evaluation</li><li>Feedback</li></ul>
                <div>Meeting ID: 123 456 789</div>
                <a href="https://teams.microsoft.com/l/meetup-join/19%3ameeting_123">Join</a>
                </body></html>""",
            },
            "attendees": [
                {"emailAddress": {"name": "John Doe", "address": "john@mayo.edu"}}
            ],
            "isAllDay": False,
            "isCancelled": False,
        }

        # Normalize the event
        normalized = client._normalize_event(raw_event)

        # Check the body was converted to clean Markdown
        assert normalized["body"]
        assert "@font-face" not in normalized["body"]
        assert "font-family:Aptos" not in normalized["body"]
        assert "<style>" not in normalized["body"]
        assert "S1 review of projects" in normalized["body"]
        assert "- AIA evaluation" in normalized["body"]
        assert "- Feedback" in normalized["body"]
        # Meeting ID should be removed
        assert "Meeting ID: 123 456 789" not in normalized["body"]
        # Link should be markdown
        assert (
            "[Join](https://teams.microsoft.com/l/meetup-join/19%3ameeting_123)"
            in normalized["body"]
        )

    def test_empty_and_minimal_html(self):
        """Test edge cases with empty or minimal HTML."""
        # Empty HTML
        assert html_to_markdown("") == ""
        assert html_to_markdown("<html></html>") == ""
        assert html_to_markdown("<html><body></body></html>") == ""

        # Just whitespace
        assert html_to_markdown("<p>   </p>") == ""
        assert html_to_markdown("<div>\n\n\n</div>") == ""

        # Minimal content
        result = html_to_markdown("<p>Hello</p>")
        assert result.strip() == "Hello"
