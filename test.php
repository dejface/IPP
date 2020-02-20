<?php
$dir = "./";
$parsePath = "parse.php";
$jexam = "/pub/courses/ipp/jexamxml/jexamxml.jar";
$recurse = false; $parse = false;
$testPassed = 0; $testFailures = 0; $jumped = 0;
$longopts = array("help", "directory:", "recursive", "parse-script:", "parse-only", "jexamxml:");
$arguments = getopt("",$longopts);

function argHandler($arguments){
    global $dir, $recurse, $parse, $parsePath;
    if ($arguments === false){
        exit(10);
    }
    if (array_key_exists("help",$arguments)){
        if($argc != 2){
            exit(10);
        }
        echo "Simple script for testing parse.php\nUsage:\n";
        echo "	--help - shows this help\n";
        echo "	--directory Path - script will look for tests in specified directory by Path\n";
        echo "	--recursive - script will look for tests in specified directory and also in all subdirectories\n";
        echo "	--parse-script File - path to parse.php\n";
        echo "	--parse-only - tests only for parse.php\n";
        echo "	--jexamxml File - specifies path to A7Soft JExamXML\n";
        exit(0);
    }

    if (array_key_exists("directory", $arguments)){
        if ($arguments["directory"] === false){
            exit (11);
        }
        $dir = $arguments["directory"];
    }
    if (array_key_exists("recursive", $arguments)){
        $recurse = true;
    }
    if (array_key_exists("parse-script",$arguments)){
        if ($arguments["parse-script"] === false){
            exit (10);
        }
        $parsePath = $arguments["parse-script"];
    }
    if (array_key_exists("parse-only",$arguments)){
        $parse = true;
    }
    if (array_key_exists("jexamxml",$arguments)){
        if ($arguments["jexamxml"] === false){
            exit (10);
        }
        $jexam = $arguments["jexamxml"];
    }
}

/*function checks directories and get all of the filePaths to array which is returned*/
function directoryCheck($dir, $recurse){
    try {
        $directory = new RecursiveDirectoryIterator($dir);
    }
    catch(Exception $error){
        fwrite(STDERR, "Directory wasn't found!\n");
        exit (11);
    }
    $testFiles = array();
    //while directory is valid
    while ($directory->valid()) {
        // check if directory is really a directory
        if ($directory->isDir()) {
            $file = $directory->current();	//current directory is stored
            if (!($file->getFilename() == '.' || $file->getFilename() == '..')){  //skipping '.' and '..' directories
                if ($recurse) {	//if recurse parameter was given
                    //calling function recursively and merging arrays
                    $testFiles = array_merge($testFiles, directoryCheck($file->getPathname(),$recurse));
                }
            }
        } else {
            //if it's a file, push it to the array
            array_push($testFiles,$directory->getPathname());
        }
        // move to the next element
        $directory->next();
    }
    return $testFiles;
}

function sortTestsToArray($testFiles){
    //arrays wich will hold *.src,*.rc,*.out files
    $sources = array();
    $arrTest = array();
    $tests = array();

    // stores source files
    foreach ($testFiles as $key){
        if (substr($key,-4,4) == ".src"){
            array_push($sources,$key);
        }
    }
    //creates an array of array with 'src', 'out' and 'rc' values
    //with corresponding keys
    foreach ($sources as $source) {
        $arrTest["src"] = $source;
        $temp = substr($source,0,-4).".rc";
        if (in_array($temp,$testFiles)){
            $arrTest["rc"] = file_get_contents($temp);
        } else {
            $arrTest["rc"] = 0;
        }
        unset($temp);

        $temp = substr($source,0,-4).".out";
        if (in_array($temp,$testFiles)){
            $arrTest["out"] = $temp;
        } else {
            $arrTest["out"] = '';
        }
        array_push($tests, $arrTest);
    }
    return $tests;
}

/*prints beginning of HTML document*/
function printHTMLHead(){
    print ("<!DOCTYPE html>
<html>
<head>
<style>
	table, th, td {
  border: 1px solid black;
}	
</style>
	<meta charset=\"utf-8\">
	<title>Results of tests</title>
</head>
<body>
<table style=\"width:100%\">
  <tr>
    <th>Test</th>
    <th>Returned code</th>
    <th>Expected return code</th>
    <th>Result</th>
  </tr>
");
}

/*prints results of tests*/
function printTest($out,$rc,$expRC,$success){
    print ("    <td>$out</td>
    <td>$rc</td>
    <td>$expRC</td>\n");

    if ($success === "PASSED"){
        print("    <td style=\"color:#32CD32\">$success</td>\n");
    } else {
        print("    <td style=\"color:#ff0000\">$success</td>\n");
    }

    print("  </tr>\n");
}

/*prints end of the HTML document*/
function printHTMLEnd($testPassed,$testFailures,$count){
    print("  <tfoot>
    <tr>
      <td colspan=\"1\" bgcolor=\"#32CD32\">TESTS SUCCEEDED $testPassed/$count</td>
      <td colspan=\"3\" bgcolor=\"#ff0000\">TESTS FAILED $testFailures/$count</td>
    </tr>
  </tfoot>
</table>
</body>
</html>\n");
}

/* this function was taken from
 * http://h4cc.de/php-check-if-xml-is-valid-with-simplexmlelement.html
 * and checks if the XML source file is valid (needed for --parse-only --recursive)
*/
function isXmlStructureValid($file) {
    $prev = libxml_use_internal_errors(true);
    $ret = true;
    try {
        new SimpleXMLElement($file, 0, true);
    } catch(Exception $e) {
        $ret = false;
    }
    if(count(libxml_get_errors()) > 0) {
        // There has been XML errors
        $ret = false;
    }
    // Tidy up.
    libxml_clear_errors();
    libxml_use_internal_errors($prev);
    return $ret;
}

/****************************************************************/
/****************************Main section************************/
/****************************************************************/

argHandler($arguments);
$testFiles = directoryCheck($dir,$recurse);
$sources = sortTestsToArray($testFiles);
printHTMLHead();

for ($i=0; $i < count($sources); $i++) {
    $output = array();

    if ($parse){
        if (isXmlStructureValid($sources[$i]["src"]) == true) {
            $jumped++;
            continue;
        }
    }
    exec("php7.4 $parsePath < ".$sources[$i]["src"],$output["out"],$output["rc"]);
    $output["out"] = implode("\n",$output["out"]);
    if ($output["rc"] == $sources["rc"]){
        $file = fopen("tempFile.out","w");
        if (!$file)
            exit(12);
        fwrite($file,$output["out"]);
        fclose($file);
        exec("java -jar $jexam ". $sources[$i]["out"]. " tempFile.out diffs.xml  /D /pub/courses/ipp/jexamxml/options",$JXout,$JXrc);
        unlink("tempFile.out");
        if ($JXrc == 0){
            $success = "PASSED";
            $testPassed++;
            printTest($sources[$i]["src"],$JXrc, $sources[$i]["rc"], $success);
        } else {
            $testFailures++;
            $success = "FAILED";
            printTest($sources[$i]["src"],$JXrc, $sources[$i]["rc"], $success);
        }
    } else {
        $testFailures++;
        $success = "FAILED";
        printTest($sources[$i]["src"],$output["rc"], $sources[$i]["rc"], $success);
    }
}
printHTMLEnd($testPassed,$testFailures, (count($sources)-$jumped));