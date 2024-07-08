import get_test_refactor_commit.GetTestRefactorCommit;
import org.junit.jupiter.api.Test;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;


public class GetTestRefactorCommitTest {
    // Test for src/main/java/getCommit.get_test_refactor_commit.GetTestRefactorCommit.java
    @Test
    public void testWriteToErrorCSV() {
        List<String> data = new ArrayList<>();
        data.add("test1");
        data.add("test2");
        GetTestRefactorCommit.writeToErrorCSV("test.csv", data);
        File file = new File("test.csv");
        assertTrue(file.exists());
        file.delete();
    }

    @Test
    public void testProcessRepositoryURL() {
        GetTestRefactorCommit.processRepositoryURL("test");
        // Test for exception
        GetTestRefactorCommit.processRepositoryURL("  ");
    }
    @Test
    public void testCheckCommitMessageTrue(){
        assertTrue(GetTestRefactorCommit.checkCommitMessage("test refactor"));
        assertTrue(GetTestRefactorCommit.checkCommitMessage("test refactoring"));
        assertTrue(GetTestRefactorCommit.checkCommitMessage("test refactored"));
        assertTrue(GetTestRefactorCommit.checkCommitMessage("testrefactoring"));
        assertTrue(GetTestRefactorCommit.checkCommitMessage("testrefactor"));
        assertTrue(GetTestRefactorCommit.checkCommitMessage("refactoredtest"));
        assertTrue(GetTestRefactorCommit.checkCommitMessage("refactortest"));
        assertTrue(GetTestRefactorCommit.checkCommitMessage("refactoringtest"));

        assertTrue(GetTestRefactorCommit.checkCommitMessage("refactoring test"));
        assertTrue(GetTestRefactorCommit.checkCommitMessage("test refactoring"));


    }

    @Test
    public void testCheckCommitMessageFalse(){
        assertFalse(GetTestRefactorCommit.checkCommitMessage("test"));
    }

    @Test
    public void testCheckChangeFile() {
        List<String> changeFiles = new ArrayList<>();
//        changeFiles.add("AAATest.java");
        changeFiles.add("src/org/opensolaris/opengrok/analysis/JFlexXref.java");
        changeFiles.add("");
        assertFalse(GetTestRefactorCommit.checkChangeFile(changeFiles));
    }

    @Test
    public void testIsTestFileName() {
        List<String> changeFiles = new ArrayList<>();
//        changeFiles.add("AAATest.java");
        changeFiles.add("src/org/opensolaris/opengrok/analysis/testJFlexXref.java");
        changeFiles.add("");
        assertTrue(GetTestRefactorCommit.isTestFileName(changeFiles));
    }


}
