import os
import pathlib as pb
import datetime as dt

class DatabaseDump:
    def __init__(self, path:pb.Path = None) -> None:
        self.path = path
        # Lista de bases de datos para dumpear, agregar más Acá
        self._database_list = [ 
            "sinteg",
            "syscam",
	    "itventory",
        ]
    
    def get_path(self) -> pb.Path:
        """Función para tener un Path por defecto donde se crearán los backups
        Defaults to postgres Home path

        Args:
            path (str, optional): Path nuevo por si se quiere colocar otro Default Path. Defaults to None.

        Returns:
            Path: Instancia del Path
        """
        if self.path is not None:
            return self.path
        
        postgres_home = os.path.expanduser("~" + "postgres")
        self.path = pb.Path(postgres_home, "BACKUPS")
        return self.path
    
    def get_bk_srv_path(self) -> pb.Path:
        return pb.Path("/","media", "MARCAJE", )
    
    def verify_connection(self) -> bool:
        """Verifica si existe el archivo "verificador" para ver si está la conexión
        con el bk-srv en Marcaje

        Returns:
            bool: Si está conectado a bk-srv = True, si no, False
        """
        bk_srv_path = pb.Path(self.get_bk_srv_path(), ".verificador")
        return bk_srv_path.exists()
    
    
    def copy_to_srv(self, db_name:str, folder_name:str, source:pb.Path):
        """Función para copiar archivos a bk-srv

        Args:
            db_name (str): Nombre de la base de datos
            folder_name (str): Nombre de la carpeta (Fecha y año)
            source (pb.Path): Destino de donde copiará
        """
        try:
            path = self.get_bk_srv_path()
            path = pb.Path(path, db_name, folder_name)
            
            os.system(f'sudo su - -c "mkdir {path} -p"')
            os.system(f'sudo su - -c "rsync -avH {source}/* {path}"')
        except Exception as err:
            print("No se pudo pasar a bk_srv, razón: ", err.args)
    
    def execute(self):
        """Función para ejecutar el Dump de las diferentes bases de datos
        cabe destacar que el DUMP se hace con el usuario "postgres"
        y se copian en su directorio raíz /var/lib/postgresql
        
        Si existe la conexión con bk-srv entonces copiará los respaldos para allá
        con el usuario root.
        
        si algún error ocurre, entonces soltará un print con el error
        """
        try:
            path:pb.Path = self.get_path()
            folder_name:str = dt.date.today().strftime("%B-%Y").upper()
            now:str = dt.datetime.now().strftime("%d-%m-%Y")
            
            for db_name in self._database_list:
                destino = pb.Path(path, db_name, folder_name)
                filename:str = "%s_%s.sql" % (db_name.upper(), now)
                
                cmd:str = f'pg_dump {db_name} > {destino}/{filename}'
                
                os.system(f'sudo su postgres -c "mkdir {destino} -p"')
                os.system(f'sudo su postgres -c "{cmd}"')
                
                if self.verify_connection():
                    self.copy_to_srv(db_name=db_name, folder_name=folder_name, source=destino)
                
        except Exception as err:
            print("Ha ocurrido un error inesperado: ", err.args)
        

dumper = DatabaseDump()
dumper.execute()
