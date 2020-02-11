<?php
/*
 * IPP Project 1
 * Author: David Oravec (xorave05)
 * File: script parse.php
 * About: This is a simple PHP script which performs lexical and syntax
 *        analysis. Script takes input from STDIN and outputs XML file
 *        to STDOUT. Input files should contain a pseudocode IPPcode20.
 *
 */

/*function which converts forbidden chars in XML to allowed ones*/
function specialChars($str){
    $str = preg_replace('/&|(\\\\046)/', "&amp;",$str);
    $str = preg_replace('/>|(\\\\076)/', "&gt;", $str);
    $str = preg_replace('/<|(\\\\074)/', "&lt;", $str);
    $str = preg_replace('/"|(\\\\042)/', "&quot;", $str);
    $str = preg_replace('/\'|(\\\\047)/', "&apos;", $str);
    return $str;
}

/*checks if the passed symbol is correct by using regular expressions
/*function returns either string,int,bool, var or exits with code 23*/
function checkSymbol($symb){
    if (preg_match('/^string@((\x5C\d{3})|[^\x23\s\x5C])*$/',$symb)){
        return (array("string" => substr(specialChars($symb),7)));
    } else if (preg_match('/^(GF|LF|TF)@[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/',$symb)){
        return (array("var" => specialChars($symb)));
    } else if (preg_match('/^bool@(true|false)$/',$symb)){
        return (array("bool" => substr($symb,5)));
    } else if (preg_match('/^int@(\-|\+)?\d+$/',$symb)){
        return (array("int" => substr($symb,4)));
    } else if (preg_match('/^nil@nil$/',$symb)){
        return (array("nil" => substr($symb,4)));
    } else {
        exit (23);
    }
}

/*array with allowed keywords (instructions) in IPPcode20*/
$keywords = array("MOVE",
    "CREATEFRAME",
    "PUSHFRAME",
    "POPFRAME",
    "DEFVAR",
    "CALL",
    "RETURN",
    "PUSHS",
    "POPS",
    "ADD",
    "SUB",
    "MUL",
    "IDIV",
    "LT",
    "GT",
    "EQ",
    "AND",
    "OR",
    "NOT",
    "INT2CHAR",
    "STRI2INT",
    "READ",
    "WRITE",
    "CONCAT",
    "STRLEN",
    "GETCHAR",
    "SETCHAR",
    "TYPE",
    "LABEL",
    "JUMP",
    "JUMPIFEQ",
    "JUMPIFNEQ",
    "EXIT",
    "DPRINT",
    "BREAK"
);

$orderCount = 0;
$comments = 0; $labels = 0; $jumps = 0; $loc = 0;
$isCreated = false;

/*processing arguments*/
$longopts = array("help", "stats:", "loc", "comments", "jumps", "labels");
$arguments = getopt("",$longopts);

if ($arguments === false){
    exit(10);
}
if (array_key_exists("help",$arguments)){
    if($argc != 2){
        exit(10);
    }
    echo "Parses input from STDIN to XML document output on stdout\nUsage:\n";
    echo "	--help - shows this help\n";
    echo "	--stats File - stats will be written into 'file'\n";
    echo "	--loc - number of lines with valid instructions (requires --stats File)\n";
    echo "	--comments - number of comments (requires --stats File)\n";
    echo "	--labels - number of labels (requires --stats File)\n";
    echo "	--jumps -  number of (un)conditioned jumps, returns and calls (requires --stats File)\n";
    exit(0);
}
if(in_array("--stats", $argv) && !array_key_exists("stats", $arguments)){
    exit(10);
}
if (array_key_exists("stats",$arguments)){
    $fileOut = fopen($arguments["stats"], "w");
    if (!$fileOut){
        exit(12);
    } else {
        $isCreated = true;
    }
}

if (!array_key_exists("stats",$arguments) &&
    (array_key_exists("loc",$arguments) ||
        array_key_exists("comments",$arguments) ||
        array_key_exists("labels",$arguments) ||
        array_key_exists("jumps",$arguments))){
    exit(10);
}

// handling header
$line = fgets(STDIN);
$line = preg_replace('/^\s*/',"",$line);
$line = preg_replace('/#.*/',"",$line);
$line = trim($line);
$line = strtoupper($line);
if (strcmp($line, ".IPPCODE20") != 0){
    fwrite(STDERR,"Wrong file header!\n");
    exit(21);
}
unset($line);

//creating XML header
$xml = new DOMDocument("1.0","UTF-8");
$xmlProgram = $xml->createElement("program");
$xmlProgram->setAttribute("language","IPPcode20");
$xml->appendChild($xmlProgram);

//main loop
do {
    $line = fgets(STDIN);
    // matching comments and storing their count in var
    $lineCorrection = preg_replace('/#.*/',"",$line,-1,$count);
    if ($count) {
        $comments += $count;
    }
    //replacing white spaces
    $lineCorrection = preg_replace('/\s*$/',"",$lineCorrection);
    $lineCorrection = preg_replace('/^\s*/',"",$lineCorrection);

    //split a line by spaces into array
    $instruction = preg_split('/[\s]+/',$lineCorrection);
    $instructionToFind = array_search(strtoupper($instruction[0]),$keywords);
    //convert instruction into "words"
    $convert = $keywords[$instructionToFind];
    $orderCount += 1;

    //if instruction wasn't find, "NONE" is added to $convert
    if ($instructionToFind === false){
        $convert = "NONE";
        $orderCount -= 1;
    }
    if (trim($lineCorrection) != ""){
        $loc += 1;
        switch($convert) {
            case "CREATEFRAME":
            case "PUSHFRAME":
            case "POPFRAME":
            case "RETURN":
            case "BREAK":
                if (count($instruction) == 1) {
                    $insertInstruction = $xml->createElement("instruction");
                    $insertInstruction->setAttribute("order", $orderCount);
                    $insertInstruction->setAttribute("opcode", strtoupper($instruction[0]));
                    $xmlProgram->appendChild($insertInstruction);

                    if (strtoupper($instruction[0]) === "RETURN"){
                        $jumps += 1;
                    }
                } else exit(23);
                break;
            case "DEFVAR":
            case "POPS":
                if (count($instruction) != 2) {
                    exit(23);
                } else if (!preg_match('/^(GF|LF|TF)@[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/', $instruction[1])) {
                    exit(23);
                } else {
                    $insertInstruction = $xml->createElement("instruction");
                    $insertInstruction->setAttribute("order", $orderCount);
                    $insertInstruction->setAttribute("opcode", strtoupper($instruction[0]));
                    $xmlProgram->appendChild($insertInstruction);

                    $insertArg1 = $xml->createElement("arg1", specialChars($instruction[1]));
                    $insertArg1->setAttribute("type", "var");
                    $insertInstruction->appendChild($insertArg1);
                }
                break;
            case "CALL":
            case "LABEL":
            case "JUMP":
                if (count($instruction) != 2) {
                    exit(23);
                } else if (!preg_match('/^[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/', $instruction[1])) {
                    exit(23);
                } else {
                    $insertInstruction = $xml->createElement("instruction");
                    $insertInstruction->setAttribute("order", $orderCount);
                    $insertInstruction->setAttribute("opcode", strtoupper($instruction[0]));
                    $xmlProgram->appendChild($insertInstruction);

                    if (strtoupper($instruction[0]) === "LABEL"){
                        $labels += 1;
                    } else {
                        $jumps += 1;
                    }

                    $insertArg1 = $xml->createElement("arg1", specialChars($instruction[1]));
                    $insertArg1->setAttribute("type", "label");
                    $insertInstruction->appendChild($insertArg1);
                }
                break;
            case "PUSHS":
            case "WRITE":
            case "EXIT":
            case "DPRINT":
                if (count($instruction) == 2) {
                    $insertInstruction = $xml->createElement("instruction");
                    $insertInstruction->setAttribute("order", $orderCount);
                    $insertInstruction->setAttribute("opcode", strtoupper($instruction[0]));
                    $xmlProgram->appendChild($insertInstruction);

                    $symbol = checkSymbol($instruction[1]);
                    $insertArg1 = $xml->createElement("arg1", reset($symbol));
                    $insertArg1->setAttribute("type", array_search(reset($symbol), $symbol));
                    $insertInstruction->appendChild($insertArg1);
                } else {
                    exit(23);
                }
                break;
            case "MOVE":
            case "INT2CHAR":
            case "NOT":
            case "STRLEN":
            case "TYPE":
                if ((count($instruction) != 3) ||
                    (!preg_match('/^(GF|LF|TF)@[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/', $instruction[1]))) {
                    exit(23);
                } else {
                    $insertInstruction = $xml->createElement("instruction");
                    $insertInstruction->setAttribute("order", $orderCount);
                    $insertInstruction->setAttribute("opcode", strtoupper($instruction[0]));
                    $xmlProgram->appendChild($insertInstruction);

                    $insertArg1 = $xml->createElement("arg1", specialChars($instruction[1]));
                    $insertArg1->setAttribute("type", "var");
                    $insertInstruction->appendChild($insertArg1);

                    $symbol = checkSymbol($instruction[2]);
                    $insertArg2 = $xml->createElement("arg2", reset($symbol));
                    $insertArg2->setAttribute("type", array_search(reset($symbol), $symbol));
                    $insertInstruction->appendChild($insertArg2);
                }
                break;
            case "ADD":
            case "SUB":
            case "MUL":
            case "IDIV":
            case "LT":
            case "GT":
            case "EQ":
            case "AND":
            case "OR":
            case "STRI2INT":
            case "CONCAT":
            case "GETCHAR":
            case "SETCHAR":
                if ((count($instruction) != 4) ||
                    (!preg_match('/^(GF|LF|TF)@[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/', $instruction[1]))) {
                    exit(23);
                } else {
                    $insertInstruction = $xml->createElement("instruction");
                    $insertInstruction->setAttribute("order", $orderCount);
                    $insertInstruction->setAttribute("opcode", strtoupper($instruction[0]));
                    $xmlProgram->appendChild($insertInstruction);

                    $insertArg1 = $xml->createElement("arg1", specialChars($instruction[1]));
                    $insertArg1->setAttribute("type", "var");
                    $insertInstruction->appendChild($insertArg1);

                    $symbol = checkSymbol($instruction[2]);
                    $insertArg2 = $xml->createElement("arg2", reset($symbol));
                    $insertArg2->setAttribute("type", array_search(reset($symbol), $symbol));
                    $insertInstruction->appendChild($insertArg2);
                    $symbol2 = checkSymbol($instruction[3]);
                    $insertArg3 = $xml->createElement("arg3", reset($symbol2));
                    $insertArg3->setAttribute("type", array_search(reset($symbol2), $symbol2));
                    $insertInstruction->appendChild($insertArg3);
                }
                break;
            case "READ":
                if ((count($instruction) != 3) ||
                    (!preg_match('/^(GF|LF|TF)@[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/', $instruction[1]))
                    || (!preg_match('/^(int|bool|string)$/',$instruction[2]))) {
                    exit(23);
                } else {
                    $insertInstruction = $xml->createElement("instruction");
                    $insertInstruction->setAttribute("order", $orderCount);
                    $insertInstruction->setAttribute("opcode", strtoupper($instruction[0]));
                    $xmlProgram->appendChild($insertInstruction);

                    $insertArg1 = $xml->createElement("arg1", specialChars($instruction[1]));
                    $insertArg1->setAttribute("type", "var");
                    $insertInstruction->appendChild($insertArg1);
                    $insertArg2 = $xml->createElement("arg2", specialChars($instruction[2]));
                    $insertArg2->setAttribute("type", "type");
                    $insertInstruction->appendChild($insertArg2);
                }
                break;
            case "JUMPIFEQ":
            case "JUMPIFNEQ":
                if ((count($instruction) != 4) ||
                    (!preg_match('/^[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/', $instruction[1]))) {
                    exit(23);
                } else {
                    $jumps += 1;
                    $insertInstruction = $xml->createElement("instruction");
                    $insertInstruction->setAttribute("order", $orderCount);
                    $insertInstruction->setAttribute("opcode", strtoupper($instruction[0]));
                    $xmlProgram->appendChild($insertInstruction);

                    $insertArg1 = $xml->createElement("arg1", specialChars($instruction[1]));
                    $insertArg1->setAttribute("type", "label");
                    $insertInstruction->appendChild($insertArg1);

                    $symbol = checkSymbol($instruction[2]);
                    $insertArg2 = $xml->createElement("arg2", reset($symbol));
                    $insertArg2->setAttribute("type", array_search(reset($symbol), $symbol));
                    $insertInstruction->appendChild($insertArg2);
                    $symbol2 = checkSymbol($instruction[3]);
                    $insertArg3 = $xml->createElement("arg3", reset($symbol2));
                    $insertArg3->setAttribute("type", array_search(reset($symbol2), $symbol2));
                    $insertInstruction->appendChild($insertArg3);
                }
                break;
            default:
                $loc -= 1;
                exit(22);
        }
    }
}while ($line);
$xml->formatOutput = true;
echo $xml->saveXML();

//writing stats into output file
foreach ($arguments as $key => $value) {
    switch ($key){
        case "loc":
            fwrite($fileOut,"$loc\n");
            break;
        case "comments":
            fwrite($fileOut,"$comments\n");
            break;
        case "labels":
            fwrite($fileOut,"$labels\n");
            break;
        case "jumps":
            fwrite($fileOut,"$jumps\n");
            break;
        case "stats":
            break;
    }
}
?>