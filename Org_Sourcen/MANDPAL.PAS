Unit MandPal;

{ Funktionen zur Palettenbelegung im Programm MandelFa.pas }

Interface

  const MaxPalette  = 3;             { # der bisher implementierten Paletten }
  type  MPType      = 0..MaxPalette;
  var   MandelPalette : MPType;

  Procedure InitializeGraphics;
  Procedure SetTVGAPalette (Nr : MPType);

Implementation {------------------------------------------------------------}

uses Graph,Crt;

var TRI16DriverMode  : integer;
    TRI256DriverMode : integer;
    GraphDriver      : integer;
    GraphMode        : integer;


(*$F+*) function AutoDetectTRI16: integer (*$F-*);
begin
  AutoDetectTRI16 := TRI16DriverMode
end;


(* AutoDetect-Funktion fÅr den TRI256 Treiber. *)

(*$F+*) function AutoDetectTRI256: integer (*$F-*);
begin
  AutoDetectTRI256 := TRI256DriverMode
end;


procedure InitializeGraphics;
var DriverNumber, ErrorCode: integer;
begin
  (* ... anderer Code ... *)
  (* Trage TRI16 Treiber in Tabelle ein und weise AutoDetect-Funktion zu *)
  DriverNumber := InstallUserDriver ('TRI16', @AutoDetectTRI16);
  if GraphResult <> grOK then begin
    WriteLn ('Fehler beim Installieren des BGI-Treibers TRI16.');
    Halt (1)
  end;

  (* Trage TRI256 Treiber in Tabelle ein und weise AutoDetect-Funktion zu *)
  DriverNumber := InstallUserDriver ('TRI256', @AutoDetectTRI256);
  if GraphResult <> grOK then begin
    WriteLn ('Fehler beim Installieren des BGI-Treibers TRI256.');
    Halt (1)
  end;

  (* Wenn die BGI Treiber Åber RegisterBGIDriver direkt in das Programm *)
  (* eingebunden werden sollen, so mu· dies an DIESER Stelle erfolgen. *)
  (* ... anderer Code ... *)
  (* Initialisierung und Umschaltung in den Graphik-Modus, *)
  (* TRI256 Modus 3, 640x480, 256 Farben *)
  GraphDriver := Detect;             (* benutze AutoDetect *)
  TRI16DriverMode := grError;        (* TRI16 Treiber ausschalten *)
  TRI256DriverMode := 3;             (* TRI256 Treiber Modus 3 *)
  InitGraph(GraphDriver, GraphMode, 'c:\tp\bgi\treesoft');
  ErrorCode := GraphResult;
  if ErrorCode <> grOK then begin
    WriteLn ('Fehler im Graphiksystem: ', GraphErrorMsg (ErrorCode));
    Halt (1)
  end;
  (* ... anderer Code ... *)
end;


PROCEDURE SetTVGAPalette (Nr : MPType);
 var r,g,b,l : integer;

 procedure sp(x,rot,gruen,blau:integer; var r,g,b:integer);
  var i : integer;

  begin
     for i := (x+1) to (x+l) do begin
        r:= r+rot  ;  if r>=64 then r:=255;
        g:= g+gruen;  if g>=64 then g:=255;
        b:= b+blau ;  if b>=64 then b:=255;
        SetRGBPalette(i,r,g,b);
     end;
     if r=255 then r:=64;
     if g=255 then g:=64;
     if b=255 then b:=64;
  end; { sp }


begin
   case Nr of 0: begin
                   l := 8;
                   r:=0;  g:=0;  b:=0;

                   sp(   0,  0,  0,  3, r,g,b);
                   sp(   8,  1,  1,  2, r,g,b);
                   sp(  16,  1,  1,  3, r,g,b);
                   sp(  24,  1,  1,  1, r,g,b);
                   sp(  32,  1,  1,  0, r,g,b);
                   sp(  40,  1,  1,  0, r,g,b);
                   sp(  48,  1,  1,  0, r,g,b);
                   sp(  56,  0,  0,  0, r,g,b);
                   sp(  64,  1,  1,  0, r,g,b);
                   sp(  72,  0,  0,  0, r,g,b);
                   sp(  80,  1,  1,  0, r,g,b);
                   sp(  88,  0,  0,  0, r,g,b);
                   sp(  96,  0,  0,  0, r,g,b);
                   sp( 104,  0,  0,  0, r,g,b);
                   sp( 112,  0,  0,  0, r,g,b);
                   sp( 120,  0,  0,  0, r,g,b);
                   sp( 128,  0,  0,  0, r,g,b);
                   sp( 136,  0,  0,  0, r,g,b);
                   sp( 144,  0,  0,  0, r,g,b);
                   sp( 152,  0,  0,  0, r,g,b);
                   sp( 160,  0,  0,  0, r,g,b);
                   sp( 168,  0,  0,  0, r,g,b);
                   sp( 176,  0,  0,  0, r,g,b);
                   sp( 184,  0,  0,  0, r,g,b);
                   sp( 192,  0,  0,  0, r,g,b);
                   sp( 200,  0,  0,  0, r,g,b);
                   sp( 208,  0,  0,  0, r,g,b);
                   sp( 216,  0,  0,  0, r,g,b);
                   sp( 224,  0,  0,  0, r,g,b);
                   sp( 232,  0,  0,  0, r,g,b);
                   sp( 240,  0,  0,  0, r,g,b);
                   sp( 248,  0,  0,  0, r,g,b);

                   SetRGBPalette(0,0,0,0);
                 end;

              1: begin
                   l := 16;
                   r:=0;  g:=0;  b:=0;

                   sp(   0,  0,  0,  1, r,g,b);
                   sp(  16,  0,  0,  1, r,g,b);
                   sp(  32,  0,  0,  1, r,g,b);
                   sp(  48,  1,  0,  1, r,g,b);
                   sp(  64,  1,  0,  0, r,g,b);
                   sp(  80,  1,  0, -1, r,g,b);
                   sp(  96,  1,  0, -1, r,g,b);
                   sp( 112,  1,  0, -1, r,g,b);
                   sp( 128,  0,  0, -1, r,g,b);
                   sp( 144,  0,  1,  0, r,g,b);
                   sp( 160,  0,  1,  0, r,g,b);
                   sp( 176,  0,  1,  0, r,g,b);
                   sp( 192,  0,  1,  0, r,g,b);
                   sp( 208,  0,  1,  0, r,g,b);
                   sp( 224,  0,  1,  0, r,g,b);
                   sp( 240,  0,  1,  0, r,g,b);

                   SetRGBPalette(0,0,0,0);
                 end;

              2: begin
                   l := 16;
                   r:=0;  g:=0;  b:=0;
                   sp(   0,  1,  0,  0, r,g,b);
                   sp(  16,  1,  0,  0, r,g,b);
                   sp(  32,  1,  0,  0, r,g,b);
                   sp(  48,  1,  1,  0, r,g,b);
                   sp(  64,  0,  1,  0, r,g,b);
                   sp(  80,  0,  2,  1, r,g,b);
                   sp(  96,  0,  0,  1, r,g,b);
                   r:=0;  g:=0;  b:=0;
                   sp( 112,  0,  0,  0, r,g,b);
                   sp( 128,  0,  0,  0, r,g,b);
                   sp( 144,  0,  0,  0, r,g,b);
                   sp( 160,  0,  0,  0, r,g,b);
                   sp( 176,  0,  0,  0, r,g,b);
                   sp( 192,  0,  0,  0, r,g,b);
                   sp( 208,  0,  0,  0, r,g,b);
                   sp( 224,  0,  0,  0, r,g,b);
                   sp( 240,  0,  0,  0, r,g,b);
                   SetRGBPalette(0,0,0,0);
                 end;
              3: begin
                   l := 16;
                   r:=0;  g:=0;  b:=0;

                   sp(   0,  0,  0,  1, r,g,b);
                   sp(  16,  0,  0,  1, r,g,b);
                   sp(  32,  0,  0,  1, r,g,b);
                   sp(  48,  1,  0,  1, r,g,b);
                   sp(  64,  1,  0,  0, r,g,b);
                   sp(  80,  1,  0, -1, r,g,b);
                   sp(  96,  1,  0, -1, r,g,b);
                   sp( 112,  1,  0, -1, r,g,b);
                   sp( 128,  0,  0, -1, r,g,b);
                   sp( 144,  0,  1,  0, r,g,b);
                   sp( 160,  0,  1,  0, r,g,b);
                   sp( 176,  0,  1,  0, r,g,b);
                   sp( 192,  0,  1,  0, r,g,b);
                   sp( 208,  0,  1,  0, r,g,b);
                   sp( 224,  0,  1,  0, r,g,b);
                   sp( 240,  0,  1,  0, r,g,b);
                   SetRGBPalette(0,0,0,0);
                 end;
   end;  { case }
end;  { SetTVGAPalette }
END.

