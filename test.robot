*** Settings ***
Library    ChromeLibrary.py
Library    SeleniumLibrary
Suite Teardown    Close Chrome

*** Variables ***
${DOWNLOAD_DIR}    ${CURDIR}${/}downloads

*** Test Cases ***
Open And Test Chrome
    [Documentation]    Launch Chrome with custom download dir and test bot.sannysoft.com
    Launch Chrome    ${DOWNLOAD_DIR}
    Connect Driver
    # Go To    https://bot.sannysoft.com/
    Go To    https://getsamplefiles.com/sample-document-files/pdf
    
    Wait Until Element Is Visible    //a[@href="https://getsamplefiles.com/download/pdf/sample-1.pdf"]
    Execute JavaScript    document.querySelector('a[href="https://getsamplefiles.com/download/pdf/sample-1.pdf"]').click()

    Sleep    5s
