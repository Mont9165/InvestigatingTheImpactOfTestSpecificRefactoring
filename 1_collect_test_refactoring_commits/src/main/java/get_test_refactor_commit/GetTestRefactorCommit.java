package get_refactor_commit;

import com.opencsv.CSVReader;
import com.opencsv.CSVReaderBuilder;
import com.opencsv.exceptions.CsvException;
import org.eclipse.jgit.api.Git;
import org.eclipse.jgit.diff.DiffEntry;
import org.eclipse.jgit.diff.Edit;
import org.eclipse.jgit.diff.EditList;
import org.eclipse.jgit.lib.Repository;
import org.eclipse.jgit.revwalk.RevCommit;
import org.eclipse.jgit.revwalk.RevTree;
import org.eclipse.jgit.treewalk.CanonicalTreeParser;
import org.eclipse.jgit.diff.DiffFormatter;
import org.eclipse.jgit.util.io.DisabledOutputStream;

import java.io.*;
import java.util.*;
import java.util.regex.Pattern;

import static github_util.OpenRepository.openRepository;

public class GetTestRefactorCommit {
    private static String CSV_OUTPUT_TEST_COMMIT_FILE;
    private static String CSV_OUTPUT_FILE;
    static List<String> repositoryErrorList = new ArrayList<>();
    static List<String> commitErrorList = new ArrayList<>();

    public static void main(String[] args) throws IOException, CsvException {
        final String FILE_NAME = "projects_info.csv";
        final String CSV_INPUT_FILE = "src/main/resources/input/" + FILE_NAME;
        CSV_OUTPUT_FILE = "src/main/resources/output/refactor_commits_" + FILE_NAME ;
        CSV_OUTPUT_TEST_COMMIT_FILE = "src/main/resources/output/refactor_commit_only_modified_test_files_" + FILE_NAME;
        final String CSV_ERROR_REPOSITORY_FILE = "src/main/resources/error/repository_" + FILE_NAME;
//         final String CSV_ERROR_COMMIT_FILE = "src/main/resources/error/commit_" + FILE_NAME;

        writeHeaderCSV();
        writeHeaderTestCommitCSV();

        FileReader csv = new FileReader(CSV_INPUT_FILE);
        CSVReader csvReader = new CSVReaderBuilder(csv).build();
        List<String[]> commitsInfo = csvReader.readAll();

        processRecords(commitsInfo);
//         writeToErrorCSV(CSV_ERROR_COMMIT_FILE, commitErrorList);
        writeToErrorCSV(CSV_ERROR_REPOSITORY_FILE, repositoryErrorList);
    }

    public static void writeToErrorCSV(String filePath, List<String> data) {
        try (FileWriter writer = new FileWriter(filePath)) {
            for (String item : data) {
                writer.append(item);
                writer.append("\n"); // 改行を追加
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public static void processRecords(List<String[]> records) {
        for (String[] record : records) {
            if (!Objects.equals(record[0], "Project Name")){
                processRepositoryURL(record[0]);
                System.out.println("Processed repository: " + record[0]);
            }
        }
    }

    public static void processRepositoryURL(String repositoryName) {
        String repoDir = "repos/" + repositoryName;
        String repositoryURL = "https://github.com/" + repositoryName;
        File inputDir = new File(repoDir);
        try {
            Repository repository = openRepository(repositoryURL+".git", inputDir);
            Git git = new Git(repository);
            processCommits(git, repoDir, repositoryURL);
        } catch (Exception e) {
            System.err.println("Error processing repository: " + e.getMessage());
            repositoryErrorList.add(repositoryURL);
        }
    }

    private static void processCommits(Git git, String repoDIr, String repositoryURL) {
        Repository repository = git.getRepository();
        try {
            Iterable<RevCommit> commits = git.log().call();
            for (RevCommit commit : commits) {
                processCommit(git, commit, repository, repoDIr, repositoryURL);
            }
        } catch (Exception e) {
            System.err.println("Error processing commits: " + e.getMessage());
            commitErrorList.add(repositoryURL);
        }
    }

    private static void processCommit(Git git, RevCommit commit, Repository repository, String repoDIr, String repositoryURL) {
        String repoName = extractRepoName(repositoryURL);
        String commitID = commit.getId().getName();
        String parentCommitID;
        String message = commit.getFullMessage();
        String commitDate = commit.getAuthorIdent().getWhen().toString();
        String author = commit.getAuthorIdent().getName();
        String commitURL = repositoryURL + "/commit/" + commitID;


        // If parentNum == 1 then this process continues
        if (checkParentCommitNumber(commit)){
            parentCommitID = commit.getParent(0).getName();
        } else {
            return;
        }

        Map<String, Object> result = getChangeFileList(git, commit, repository);
        List<String> changedFiles = (List<String>) result.get("changedFiles");
        int[] lineCounts = (int[]) result.get("lineCounts");
        int totalAdditions = lineCounts[0];
        int totalDeletions = lineCounts[1];

        if ((checkChangeFiles(changedFiles) || isTestFilesName(changedFiles)) && checkCommitMessage(message)){
            writeCommitToCSV(repoName, repositoryURL, commitID, parentCommitID, commitURL, message, commitDate, author, changedFiles);
            if (isOnlyTestFilesChanged(changedFiles)){
                writeTestCommitToCSV(repoName, repositoryURL, commitID, parentCommitID, commitURL, commitDate, String.valueOf(changedFiles.size()), String.valueOf(totalAdditions), String.valueOf(totalDeletions));
            }
        }
        System.out.println(repoName + ": processed (" + commitID + ")");
    }

    private static void writeTestCommitToCSV(String repoName, String repositoryURL, String commitID, String parentCommitID, String commitURL, String commitDate, String changedFilesCount, String totalAdditions, String totalDeletions) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(CSV_OUTPUT_TEST_COMMIT_FILE, true))) {
            writer.write(String.join(",", Arrays.asList(
                    repoName,
                    repositoryURL,
                    commitID,
                    parentCommitID,
                    commitURL,
                    commitDate,
                    changedFilesCount,
                    totalAdditions,
                    totalDeletions
            )));
            writer.newLine();
        } catch (IOException e) {
            System.err.println("Error writing commit to CSV file: " + e.getMessage());
        }
    }

    private static boolean isOnlyTestFilesChanged(List<String> changedFiles) {
        for (String file : changedFiles){
            if (!isTestFileName(file)){
                return false;
            }
        }
        return true;
    }

    private static boolean isTestFileName(String file){
        String[] parts = file.split("/");
        String fileName = parts[parts.length - 1];
        if (file.endsWith("test.java") || file.endsWith("Test.java")){
            return true;
        }
        return (fileName.startsWith("test") || fileName.startsWith("Test")) && file.endsWith(".java");
    }

    public static boolean isTestFilesName(List<String> changedFiles) {
        for (String file : changedFiles){
            String[] parts = file.split("/");
            String fileName = parts[parts.length - 1];
            if ((fileName.startsWith("test") || fileName.startsWith("Test")) && file.endsWith(".java")){
                return true;
            }
        }
        return false;
    }


    public static boolean checkCommitMessage(String message) {
        String lowerCaseMessage = message.toLowerCase();
        // test* のパターン
        boolean containsTestPattern = Pattern.compile("\\btest\\w*\\b").matcher(lowerCaseMessage).find();
        // refactor* のパターン
        boolean containsRefactorPattern = Pattern.compile("\\brefactor\\w*\\b").matcher(lowerCaseMessage).find();
        // 両方のパターンが見つかった場合に true を返す
        return containsTestPattern && containsRefactorPattern;
    }

    public static boolean checkChangeFiles(List<String> changedFiles) {
        for (String file : changedFiles){
            if (file.endsWith("test.java") || file.endsWith("Test.java")){
                return true;
            }
        }
        return false;
    }

    private static boolean checkParentCommitNumber(RevCommit commit) {
        return commit.getParentCount() == 1;
    }

    private static void writeCommitToCSV(String repoName, String repositoryURL, String commitID, String parentCommitID, String commitURL, String message, String commitDate, String author, List<String> changedFiles) {
        message = "\"" + message.replaceAll("\"", "\"\"") + "\"";
        String files = "[" + String.join(" ", changedFiles) + "]";

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(CSV_OUTPUT_FILE, true))) {
            writer.write(String.join(",", Arrays.asList(
                    repoName,
                    repositoryURL,
                    commitID,
                    parentCommitID,
                    commitURL,
                    message,
                    commitDate,
                    author,
                    files
            )));
            writer.newLine();
        } catch (IOException e) {
            System.err.println("Error writing commit to CSV file: " + e.getMessage());
        }
    }


    private static Map<String, Object> getChangeFileList(Git git, RevCommit commit, Repository repository) {
        List<String> changedFiles = new ArrayList<>();
        int totalAdditions = 0;
        int totalDeletions = 0;

        try {
            RevTree parentTree = commit.getParent(0).getTree();
            RevTree commitTree = commit.getTree();

            CanonicalTreeParser parentTreeParser = new CanonicalTreeParser();
            CanonicalTreeParser commitTreeParser = new CanonicalTreeParser();

            parentTreeParser.reset(repository.newObjectReader(), parentTree.getId());
            commitTreeParser.reset(repository.newObjectReader(), commitTree.getId());

            List<DiffEntry> diffs = git.diff()
                    .setNewTree(commitTreeParser)
                    .setOldTree(parentTreeParser)
                    .call();

            try (DiffFormatter diffFormatter = new DiffFormatter(DisabledOutputStream.INSTANCE)) {
                diffFormatter.setRepository(repository);

                for (DiffEntry diff : diffs) {
                    changedFiles.add(diff.getNewPath());

                    EditList edits = diffFormatter.toFileHeader(diff).toEditList();
                    for (Edit edit : edits) {
                        totalAdditions += edit.getEndB() - edit.getBeginB(); // 追加行数
                        totalDeletions += edit.getEndA() - edit.getBeginA(); // 削除行数
                    }
                }
            }

        } catch (Exception e) {
            System.err.println("Error getting changed files: " + e.getMessage());
        }
        Map<String, Object> result = new HashMap<>();
        result.put("changedFiles", changedFiles);
        result.put("lineCounts", new int[]{totalAdditions, totalDeletions});

        return result;
    }

    public static String extractRepoName(String repository) {
        String prefix = "https://github.com/";
        if (repository.startsWith(prefix)) {
            return repository.substring(prefix.length());
        }
        return "";
    }

    private static void writeHeaderCSV() {
        List<String> header = Arrays.asList(
                "repository_name",
                "repository_url",
                "commit_id",
                "parent_commit_id",
                "commit_url",
                "commit_message",
                "commit_date",
                "commit_author",
                "changed_files"
        );

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(GetTestRefactorCommit.CSV_OUTPUT_FILE))) {
            writer.write(String.join(",", header));
            writer.newLine();
        } catch (IOException e) {
            System.err.println("Error writing header to CSV file: " + e.getMessage());
        }
    }

    private static void writeHeaderTestCommitCSV() {
        List<String> header = Arrays.asList(
                "repository_name",
                "repository_url",
                "commit_id",
                "parent_commit_id",
                "commit_url",
                "commit_date",
                "changed_files_count",
                "total_addition_lines",
                "total_deletions_lines"
        );
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(GetTestRefactorCommit.CSV_OUTPUT_TEST_COMMIT_FILE))) {
            writer.write(String.join(",", header));
            writer.newLine();
        } catch (IOException e) {
            System.err.println("Error writing header to CSV file: " + e.getMessage());
        }
    }

}
