import pandas as pd
import logging
from typing import List, Dict, Any
from src.utils.calculations import WorkforceCalculator
from src.data_processing.data_loader import DataLoader

logger = logging.getLogger(__name__)

class PopupCreator:
    """Creates HTML popup content for map markers."""
    
    def __init__(self):
        self.calculator = WorkforceCalculator()
    
    def create_basic_popup(self, row: pd.Series, include_workers: bool = True) -> str:
        """
        Create basic popup content for parks/cemeteries.
        
        Args:
            row: Data row with location information
            include_workers: Whether to include worker calculations
            
        Returns:
            HTML string for popup content
        """
        try:
            content = f"""
            <b>{row.get('name', 'Unknown')}</b><br>
            Größe: {row.get('area_ha', 0):.2f} ha<br>
            Manager: {row.get('manager_name', 'N/A')}<br>
            E-Mail: <a href='mailto:{row.get('email', '')}'>{row.get('email', 'N/A')}</a><br>
            Telefon: {row.get('phone', 'N/A')}<br>
            Website: <a href='{row.get('website', '')}' target='_blank'>Link</a><br>
            """
            
            if include_workers and 'area_ha' in row:
                workers = self.calculator.calculate_required_workers(row['area_ha'])
                bikes = self.calculator.calculate_required_bikes(workers)
                content += f"""
                <b>Benötigte Arbeiter:</b> {workers}<br>
                <b>Anzahl Fahrräder:</b> {bikes}
                """
            
            return content
            
        except Exception as e:
            logger.error(f"Error creating basic popup: {e}")
            return "<b>Error loading data</b>"
        
    def create_basic_popup_camping(self, row: pd.Series, include_workers: bool = True) -> str:
        """
        Create basic popup content for parks/cemeteries.
        
        Args:
            row: Data row with location information
            include_workers: Whether to include worker calculations
            
        Returns:
            HTML string for popup content
        """
        try:
            content = f"""
            <b>{row.get('name', 'Unknown')}</b><br>
            Größe: {row.get('area_ha', 0):.2f} ha<br>
            Manager: {row.get('manager_name', 'N/A')}<br>
            E-Mail: <a href='mailto:{row.get('email', '')}'>{row.get('email', 'N/A')}</a><br>
            Telefon: {row.get('phone', 'N/A')}<br>
            Adresse:{row.get('adresse')}<br>
            Website: <a href='{row.get('website', '')}' target='_blank'>Link</a><br>
            """
            
            if include_workers and 'area_ha' in row:
                workers = self.calculator.calculate_required_workers(row['area_ha'])
                bikes = self.calculator.calculate_static_bikes()
                content += f"""
                <b>Benötigte Arbeiter:</b> {workers}<br>
                <b>Anzahl Fahrräder:</b> {bikes}
                """
            return content

        except Exception as e:
            logger.error(f"Error creating basic popup: {e}")
            return "<b>Error loading data</b>"
            
            
    
    def create_city_summary_popup(self, city: str, parks_data: pd.DataFrame, 
                                cemetery_data: pd.DataFrame, camping_data: pd.DataFrame, size_threshold: float) -> str:
        """
        Create popup content for city summary markers.
        
        Args:
            city: City name
            parks_data: Parks data for the city
            cemetery_data: Cemetery data for the city
            size_threshold: Size threshold for categorization
            
        Returns:
            HTML string for popup content
        """
        try:
            # Calculate statistics
            stats = self._calculate_city_statistics(parks_data, cemetery_data, size_threshold)
            
            # Create contact table
            contacts_table = self._create_contacts_table(parks_data, cemetery_data, camping_data)
            
            content = f"""
            <b>{city}</b><br>
            Anzahl der Parks: {stats['total_parks']}<br>
            Parks über Schwellenwert: {stats['parks_above_threshold']}<br>
            Gesamte Fläche Parks: {stats['total_parks_area']:.2f} ha<br>
            Anzahl der Friedhöfe: {stats['total_cemeteries']}<br>
            Friedhöfe über Schwellenwert: {stats['cemeteries_above_threshold']}<br>
            Gesamte Fläche Friedhöfe: {stats['total_cemeteries_area']:.2f} ha<br>
            Benötigte Arbeiter: {stats['total_workers']}<br>
            Anzahl Fahrräder: {stats['total_bikes']}<br>
            Kontaktinformationen:<br>{contacts_table}
            """
            
            return content
            
        except Exception as e:
            logger.error(f"Error creating city summary popup for {city}: {e}")
            return f"<b>{city}</b><br>Error loading data"
    
    def _calculate_city_statistics(self, parks_data: pd.DataFrame, 
                                 cemetery_data: pd.DataFrame, size_threshold: float) -> Dict[str, Any]:
        """Calculate statistics for a city."""
        # Add worker calculations if not present
        if 'arbeiter' not in parks_data.columns:
            parks_data['arbeiter'] = parks_data['area_ha'].apply(
                self.calculator.calculate_required_workers
            )
            parks_data['fahrraeder'] = parks_data['arbeiter'].apply(
                self.calculator.calculate_required_bikes
            )
        
        if 'arbeiter' not in cemetery_data.columns:
            cemetery_data['arbeiter'] = cemetery_data['area_ha'].apply(
                self.calculator.calculate_required_workers
            )
            cemetery_data['fahrraeder'] = cemetery_data['arbeiter'].apply(
                self.calculator.calculate_required_bikes
            )
        
        return {
            'total_parks': len(parks_data),
            'total_parks_area': parks_data["area_ha"].sum(),
            'total_cemeteries': len(cemetery_data),
            'total_cemeteries_area': cemetery_data["area_ha"].sum(),
            'parks_above_threshold': len(parks_data[parks_data['area_ha'] > size_threshold]),
            'cemeteries_above_threshold': len(cemetery_data[cemetery_data['area_ha'] > size_threshold]),
            'total_workers': parks_data["arbeiter"].sum() + cemetery_data["arbeiter"].sum(),
            'total_bikes': parks_data["fahrraeder"].sum() + cemetery_data["fahrraeder"].sum()
        }
    
    def _create_contacts_table(self, parks_data: pd.DataFrame, cemetery_data: pd.DataFrame, camping_data: pd.DataFrame) -> str:
        """Create HTML table for contact information."""
        contacts_table = """
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr><th>Manager</th><th>Telefon</th><th>E-Mail</th><th>Website</th></tr>
        """
        
        # Collect unique contacts
        all_contacts = []
        
        for data in [parks_data, cemetery_data, camping_data]:
            if not data.empty:
                for _, row in data.iterrows():
                    contact = {
                        'manager': row.get('manager_name', ''),
                        'phone': str(row.get('phone', '')),
                        'email': row.get('email', ''),
                        'website': row.get('website', '')
                    }
                    if contact not in all_contacts:
                        all_contacts.append(contact)
        
        # Add contact rows
        for contact in all_contacts:
            email_link = f"<a href='mailto:{contact['email']}'>{contact['email']}</a>" if contact['email'] else ""
            website_link = f"<a href='{contact['website']}' target='_blank'>Link</a>" if contact['website'] else ""
            
            contacts_table += f"""
            <tr>
                <td>{contact['manager']}</td>
                <td>{contact['phone']}</td>
                <td>{email_link}</td>
                <td>{website_link}</td>
            </tr>
            """
        
        contacts_table += "</table>"
        return contacts_table

# Usage in main application would be:
# from src.data_processing.data_loader import DataLoader
# from src.visualization.popup_creator import PopupCreator
# from config.settings import Config

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Load data
    loader = DataLoader()
    parks_data = loader.load_parks_data()
    
    
    print(f"Loaded {len(parks_data['df'])} parks records")