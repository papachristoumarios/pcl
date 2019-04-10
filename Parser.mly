/*  Tokens */
%token T_eof
%token T_integer_constant
%token T_real_constant
%token T_name
%token T_character
%token T_string
%token T_and
%token T_do
%token T_if
%token T_of
%token T_then
%token T_array
%token T_else
%token T_integer
%token T_or
%token T_true
%token T_begin
%token T_end
%token T_label
%token T_procedure
%token T_var
%token T_boolean
%token T_false
%token T_mod
%token T_program
%token T_while
%token T_char
%token T_forward
%token T_new
%token T_real
%token T_dispose
%token T_function
%token T_nil
%token T_result
%token T_div
%token T_goto
%token T_not
%token T_return
%token T_eq
%token T_gt
%token T_lt
%token T_gte
%token T_lte
%token T_neq
%token T_plus
%token T_minus
%token T_times
%token T_frac
%token T_exp
%token T_ptr
%token T_lparen
%token T_rparen
%token T_set
%token T_semicolon
%token T_dot
%token T_comma
%token T_lsquare
%token T_rsquare
%token T_ddot
%token T_comment

/* Start symbol */
%start program

/* Types */
%type <unit> program

/* Precendencies & Associativity */
%nonassoc T_eq T_gt T_lt T_gte T_lte T_neq
%left T_plus T_minus
%left T_times T_frac T_div T_mod
%left T_neg
%right T_exp
%left T_ptr
%%

program : T_program T_name T_semicolon body T_dot { () }

body : local_list block { () }

local_list:  { () }
            | local local_list { () }

local : T_var complex_ids complex_ids_list { () }
        | T_forward header T_semicolon { () }
        | header T_semicolon body T_semicolon { () }
        | T_label T_name id_list T_semicolon { () }

complex_ids : T_name id_list T_set type T_semicolon { () }

complex_ids_list : { () } | complex_ids complex_ids_list { () }

id_list: { () } | T_comma T_name id_list { () }

header : T_procedure T_name T_lparen formal_opt T_rparen { () }
         | T_function T_name T_lparen formal_opt T_rparen T_ddot type { () }

formal_opt : { () } | formal formal_list { () }

formal_list : { () } | T_semicolon formal formal_list { () }

formal : var_opt T_name id_list T_semicolon type { () }

var_opt : { () } | T_var { () }

type : T_integer { () }
      | T_real { () }
      | T_boolean { () }
      | T_char { () }
      | T_array array_length_opt T_of type { () }
      | T_exp type { () }

array_length_opt : { () } | T_lsquare T_integer_constant T_rsquare { () }

block : T_begin stmt stmt_list T_end { () }

stmt_list : { () } | T_semicolon stmt stmt_list { () }

/*  Statements */
stmt : { () }
      | l_value T_set expr { () }
      | block { () }
      | call { () }
      | if_stmt { () }
      | T_while expr T_do stmt { () }
      | T_name T_ddot stmt { () }
      | T_goto T_name { () }
      | T_return { () }
      | T_new l_value { () }
      | T_new T_lsquare expr T_rsquare l_value { () }
      | T_dispose l_value { () }
      | T_dispose T_lsquare T_rsquare l_value { () }


if_stmt: T_if expr T_then else_stmt { () }

else_stmt: T_else stmt { () } | { () }

/*  Expressions */
expr : l_value { () }
      | r_value { () }

/* L-values and R-values */
l_value : T_name { () }
        | T_result { () }
        | T_string { () }
        | l_value T_lsquare expr T_rsquare { () }
        | expr T_exp { () }
        | T_lparen l_value T_rparen { () }

r_value : T_integer_constant { () }
        | T_true { () }
        | T_false { () }
        | T_real_constant { () }
        | T_character { () }
        | T_nil { () }
        | T_lparen r_value T_rparen { () }
        | call { () }
        | T_ptr l_value { () }
        | unop expr { () }
        | expr binop expr { () }

/* Calls */
call : T_name T_lparen argument_opt T_rparen { () }

argument_opt : { () }
              | expr { () }
              | expr T_comma argument_list { () }

argument_list : { () }
              | expr T_comma argument_list { () }

/* Unary Operators */
unop : T_not { () }
      | T_plus { () }
      | T_minus { () }

/* Binary Operators */
binop : T_plus { () }
        | T_minus { () }
        | T_times { () }
        | T_frac { () }
        | T_div { () }
        | T_mod { () }
        | T_or { () }
        | T_and { () }
        | T_neq { () }
        | T_eq { () }
        | T_lt { () }
        | T_gt { () }
        | T_lte { () }
        | T_gte { () }
