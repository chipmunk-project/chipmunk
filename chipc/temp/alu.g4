grammar alu;

// Hide whitespace, but don't skip it
WS : [ \n\t\r]+ -> channel(HIDDEN);
LINE_COMMENT : '//' ~[\r\n]* -> skip;
// Keywords
RELOP            : 'rel_op'; // <, >, <=, >=, ==, !=
ARITHOP          : 'arith_op'; // +,-
MUX3             : 'Mux3';   // 3-to-1 mux
MUX2             : 'Mux2';   // 2-to-1 mux
OPT              : 'Opt';    // Pick either the argument or 0
CONSTANT         : 'C()'; // Return a finite constant
TRUE             : 'True';   // Guard corresponding to "always update"
IF               : 'if';
ELSE             : 'else';
ELIF             : 'elif';
RETURN           : 'return';
EQUAL            : '==';
GREATER          : '>';
LESS             : '<';
GREATER_OR_EQUAL : '>=';
LESS_OR_EQUAL    : '<=';
NOT_EQUAL        : '!=';
OR               : '||';
AND              : '&&';

// Identifiers
ID : ('a'..'z' | 'A'..'Z') ('a'..'z' | 'A'..'Z' | '_' | '0'..'9')*;

// Numerical constant
NUM : ('0'..'9') | (('1'..'9')('0'..'9')+);


// alias id to state_var and packet_field
state_var    : ID;
packet_field : ID;
// alias id to hole variables
hole_var : ID;

// Determines whether the ALU is stateless or stateful
stateless : 'stateless';
stateful  : 'stateful';
state_indicator : stateless
                | stateful;

// list of state_var
state_var_with_comma : ',' state_var;
state_vars : 'void' // Used if we do not want any state vars
           | state_var
           | state_var state_var_with_comma+;

// Represents the holes in the stateless .j2 files
hole_var_with_comma : ',' hole_var;
hole_vars : 'void' // Used if we do not want hole vars
          | hole_var
          | hole_var hole_var_with_comma+
          ;

// list of packet_field
packet_field_with_comma : ',' packet_field;
packet_fields : packet_field
              | packet_field packet_field_with_comma+ ;


// guard for if and elif statements
guard  : guard (EQUAL
              | GREATER
              | GREATER_OR_EQUAL
              | LESS
              | LESS_OR_EQUAL
              | NOT_EQUAL
              | AND
              | OR) guard #Nested 
       | '(' guard ')' #Paren
       | RELOP '(' expr ',' expr ')' #RelOp
       | expr EQUAL expr #Equals
       | expr GREATER expr #Greater
       | expr GREATER_OR_EQUAL expr #GreaterEqual
       | expr LESS expr #Less
       | expr LESS_OR_EQUAL expr #LessEqual
       | expr NOT_EQUAL expr #NotEqual
       | expr AND expr #And
       | expr OR expr #Or
       | TRUE #True
       ;


// alu_body
alu_body : alu_update = updates
         | return_update = return_statement
         | IF '(' if_guard = guard ')' '{' if_body =  alu_body '}' (ELIF '(' elif_guard = guard ')' '{' elif_body = alu_body '}')* (ELSE  '{' else_body = alu_body '}')?
         ;
 
return_statement : RETURN expr ';';


updates: update+;
update : state_var '=' expr ';';

expr   : state_var #StateVar
       | hole_var #HoleVar
       | packet_field #PacketField
       | expr op=('+'|'-'|'*'|'/') expr #ExprWithOp
       | '(' expr ')' #ExprWithParen
       | MUX3 '(' expr ',' expr ',' NUM ')' #Mux3WithNum
       | MUX3 '(' expr ',' expr ',' expr ')' #Mux3
       | MUX2 '(' expr ',' expr ')' #Mux2
       | OPT '(' expr ')' #Opt
       | CONSTANT #Constant
       | ARITHOP '(' expr ',' expr ')' # ArithOp
       | NUM #Value
       ;

alu: state_indicator state_vars hole_vars packet_fields alu_body;