<?php
function specialChars($str){
    $str = preg_replace('/&/', "&amp",$str);
    $str = preg_replace('/>/', "&gt", $str);
    $str = preg_replace('/</', "&lt", $str);
    $str = preg_replace('/"/', "&quot", $str);
    $str = preg_replace('/\'/', "&apos", $str);
    return $str;
}

function checkSymbol($symb){
    if (preg_match('/^string\x40((\x5C\d{3})|[^\x23\s\x5C])*$/',$symb)){
        return (array("string" => substr(specialChars($symb),7)));
    } else if (preg_match('/^(GF|LF|TF)\x40[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/',$symb)){
        return (array("var" => specialChars($symb)));
    } else if (preg_match('/^bool\x40(true|false)$/',$symb)){
        return (array("bool" => substr($symb,5)));
    } else if (preg_match('/^int\x40(\x2D|\x2B)?\d+$/',$symb)){
        return (array("int" => substr($symb,4)));
    } else {
        exit (23);
    }
}

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
$longopts = array("help");
$arguments = getopt("",$longopts);

if (count($argv) != 1){
    if (count($argv) != count($arguments) + 1){
        exit(10);
    } else if (count($arguments) == 1 && array_key_exists("help",$arguments)){
        echo "Parses input from STDIN to XML document output on stdout\nUsage:\n";
        echo "	--help - shows this help\n";
        exit(0);
    } else {
        exit(10);
    }
}


//$line = fgets(STDIN);
$handle = fopen("C:\Users\orave\PhpstormProjects\IPP\Project1\lolik","r");
$line = fgets($handle);
$line = trim($line);
$line = strtoupper($line);
if (strcmp($line, ".IPPCODE20") != 0){
    fwrite(STDERR,"Wrong file header!\n");
    exit(21);
}
unset($line);

$xml = new DOMDocument("1.0","UTF-8");
$xmlProgram = $xml->createElement("program");
$xmlProgram->setAttribute("language","IPPcode20");
$xml->appendChild($xmlProgram);
//echo $xml->saveXML();

do {
    $line = fgets($handle);

    $lineCorrection = preg_replace('/\s*$/',"",$line);
    $lineCorrection = preg_replace('/^\s*/',"",$lineCorrection);

    $instruction = preg_split('/[\s]+/',$lineCorrection);
    $instructionToFind = array_search(strtoupper($instruction[0]),$keywords);
    $convert = $keywords[$instructionToFind];
    $orderCount += 1;
if (trim($lineCorrection) != ""){
    switch($convert) {
        case "CREATEFRAME":
        case "PUSHFRAME":
        case "POPFRAME":
        case "RETURN":
        case "BREAK":
            if (count($instruction) == 1) {
                //echo $instruction[0];
                $insertInstruction = $xml->createElement("instruction");
                $insertInstruction->setAttribute("order", $orderCount);
                $insertInstruction->setAttribute("opcode", strtoupper($instruction[0]));
                $xmlProgram->appendChild($insertInstruction);
                // echo $xml->saveXML();
            } else exit(23);
            break;
        case "DEFVAR":
        case "POPS":
            if (count($instruction) != 2) {
                exit(23);
            } else if (!preg_match('/^(GF|LF|TF)\x40[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/', $instruction[1])) {
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
        case "STRLEN":
        case "TYPE":
            if ((count($instruction) != 3) ||
                (!preg_match('/^(GF|LF|TF)\x40[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/', $instruction[1]))) {
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
        case "NOT":
        case "STRI2INT":
        case "CONCAT":
        case "GETCHAR":
        case "SETCHAR":
            if ((count($instruction) != 4) ||
                (!preg_match('/^(GF|LF|TF)\x40[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/', $instruction[1]))) {
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
                (!preg_match('/^(GF|LF|TF)\x40[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/', $instruction[1]))
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
        /*default:
            exit(22);*/
    }

    }
}while ($line);
$xml->formatOutput = true;
echo $xml->saveXML();
?>
